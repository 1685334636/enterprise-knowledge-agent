"""受限本地检索工具。资料是数据，工具不执行资料里的指令。"""
import json
import re
import sqlite3
from pathlib import Path

from .models import Corpus


STOP_TERMS = {"可以", "多少", "多久", "怎么", "请问", "一下", "这个", "问题", "我们", "公司", "是否", "什么", "关于", "相关"}


class KnowledgeStore:
    def __init__(self, corpus_path: Path, aliases_path: Path | None = None):
        self.corpus_path = Path(corpus_path)
        self.corpus = Corpus.model_validate_json(self.corpus_path.read_text(encoding="utf-8"))
        self.aliases = {}
        if aliases_path is not None:
            self.aliases = json.loads(Path(aliases_path).read_text(encoding="utf-8"))["aliases"]
        self._passages = {}
        self._db = sqlite3.connect(":memory:")
        self._db.execute("CREATE VIRTUAL TABLE passages USING fts5(passage_id UNINDEXED, tokens)")
        for document in self.corpus.documents:
            for passage in document.passages:
                metadata = {"doc_id":document.doc_id,"title":document.title,
                            "version_date":document.version_date.isoformat(),"scope":document.scope,
                            **passage.model_dump()}
                self._passages[passage.passage_id] = metadata
                tokens = self.tokenize(document.title+" "+document.scope+" "+passage.text)
                self._db.execute("INSERT INTO passages VALUES (?,?)", (passage.passage_id," ".join(tokens)))
        self._db.commit()

    def normalize(self, text):
        result = text.lower()
        # 一次替换避免别名替换后再次匹配导致循环增长。
        if self.aliases:
            pattern = "|".join(re.escape(k) for k in sorted(self.aliases,key=len,reverse=True))
            result = re.sub(pattern,lambda m:self.aliases[m.group()],result)
        return result

    def tokenize(self, text):
        text = self.normalize(text)
        for stop in STOP_TERMS:
            text = text.replace(stop," ")
        tokens = []
        for part in re.findall(r"[a-z0-9]+(?:\.[0-9]+)?|[\u4e00-\u9fff]+",text):
            if re.fullmatch(r"[\u4e00-\u9fff]+",part):
                tokens.extend([part] if len(part)==1 else [part[i:i+2] for i in range(len(part)-1)])
            else:
                tokens.append(part)
        return tokens

    def search(self, query, top_k=5):
        if not isinstance(query,str) or not query.strip() or len(query)>500:
            raise ValueError("query必须为1至500字符的非空字符串")
        if not isinstance(top_k,int) or isinstance(top_k,bool) or not 1<=top_k<=8:
            raise ValueError("top_k必须为1至8的整数")
        terms = list(dict.fromkeys(self.tokenize(query)))[:40]
        if not terms:
            return {"hits":[],"query":query,"token_count":0}
        match = " OR ".join('"'+term.replace('"','""')+'"' for term in terms)
        found = self._db.execute(
            "SELECT passage_id,bm25(passages) AS score FROM passages WHERE passages MATCH ? ORDER BY score,passage_id LIMIT ?",
            (match,top_k)).fetchall()
        hits = []
        for passage_id,score in found:
            p = self._passages[passage_id]
            hits.append({k:p[k] for k in ("doc_id","passage_id","title","version_date","scope","fact_key")} |
                        {"snippet":p["text"][:26]+("…" if len(p["text"])>26 else ""),"score":round(float(score),8)})
        return {"hits":hits,"query":query,"token_count":len(terms)}

    def read(self, passage_id):
        if not re.fullmatch(r"[A-Z][A-Z0-9_-]*:P[0-9]+",str(passage_id)):
            raise ValueError("只允许读取已登记的片段ID，禁止文件路径")
        if passage_id not in self._passages:
            raise KeyError("片段ID不存在")
        return dict(self._passages[passage_id])

    def close(self):
        self._db.close()


class ToolExecutor:
    def __init__(self, store, fail_once=None, always_fail=None):
        self.store = store
        valid = {"search_documents","read_passage",None}
        if fail_once not in valid or always_fail not in valid:
            raise ValueError("无效故障注入工具")
        self.fail_once,self.always_fail = fail_once,always_fail
        self._failed_once = False

    def execute(self, action, arguments):
        if action not in {"search_documents","read_passage"}:
            raise ValueError("工具不在允许列表中")
        if action==self.always_fail or (action==self.fail_once and not self._failed_once):
            self._failed_once = True
            return {"ok":False,"error":{"code":"TOOL_UNAVAILABLE","message":"工具暂时不可用（显式故障注入）"},"result":None}
        try:
            if action=="search_documents":
                result = self.store.search(**arguments)
            else:
                result = self.store.read(**arguments)
            return {"ok":True,"error":None,"result":result}
        except (ValueError,KeyError,sqlite3.Error) as exc:
            code = "NOT_FOUND" if isinstance(exc,KeyError) else "INVALID_TOOL_ARGUMENTS"
            return {"ok":False,"error":{"code":code,"message":"工具执行失败，参数不合法或资料不存在"},"result":None}
