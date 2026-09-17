"""文档规则的简化可执行模型；不调用Liveo、设备、数据库，不模拟机械可靠性。"""
from dataclasses import dataclass, field, asdict
from copy import deepcopy
from pathlib import Path
import json

class Refused(Exception): pass

def require(ok, reason):
    if not ok: raise Refused(reason)

@dataclass
class Model:
    # 单资产/单通道；额度部分用多任务演示同一主体并发申请的串行裁定结果。
    online: bool = True
    safe: bool = True
    location: str = 'stock'
    clean: bool = True
    frozen: bool = False
    loaded: bool = True
    epoch: int = 1
    assignment: int = 1
    cycle: int = 0
    owner: str = ''
    reservation_limit: int = 1
    period_used: int = 0
    reservations: set = field(default_factory=set)
    commands: dict = field(default_factory=dict)
    tasks: dict = field(default_factory=dict)
    loan: str = ''
    loans: dict = field(default_factory=dict)
    return_sessions: dict = field(default_factory=dict)
    receipts: dict = field(default_factory=dict)
    received: set = field(default_factory=set)
    applied: set = field(default_factory=set)
    motion_starts: int = 0
    release_count: int = 0

    def authorize(self, cid, authorized=True):
        require(self.online and authorized, '无在线授权')
        if cid in self.tasks: return
        require(len(self.reservations)+bool(self.loan)<self.reservation_limit,'额度占用')
        self.reservations.add(cid)
        self.tasks[cid]={'status':'AUTHORIZED','cycle':None,'permit':False,'executed':False}

    def accept(self,cid,payload='ISSUE_ONE',assignment=None,epoch=None):
        require(cid in self.tasks,'任务不存在')
        old=self.commands.get(cid)
        if old:
            require(old['payload']==payload,'同ID内容冲突')
            return old['state']
        require(self.online and self.safe,'未满足接受条件')
        require((self.assignment if assignment is None else assignment)==self.assignment,'旧归属')
        require((self.epoch if epoch is None else epoch)==self.epoch,'旧通道轮次')
        require(not self.owner,'通道已占用')
        self.commands[cid]={'payload':payload,'state':'ACCEPTED'}
        self.owner=cid
        return 'ACCEPTED'

    def cancel(self,cid):
        require(cid in self.tasks,'原任务不存在')
        c=self.commands.get(cid)
        require(not c or c['state'] in ('ACCEPTED','CANCELLED'),'动作已开始或未知')
        self.commands[cid]={'payload':'ISSUE_ONE','state':'CANCELLED'}
        self.tasks[cid]['status']='CANCELLED_NO_EXECUTION'
        self.reservations.discard(cid)
        if self.owner==cid:self.owner=''

    def start(self,cid):
        c=self.commands[cid]
        if c['state'] in ('STARTED','DONE'):return
        require(c['state']=='ACCEPTED' and self.safe,'不允许启动')
        require(self.owner==cid,'无执行权')
        c['state']='STARTED' # 模型把持久化开始意图作为不可重试边界
        self.tasks[cid]['executed']=True
        self.motion_starts+=1
        self.location='held'

    def permit(self,cid):
        t=self.tasks[cid]
        if t['permit']:return
        require(self.online and self.location=='held' and self.owner==cid,'未保持或离线')
        require(self.clean and self.loaded and not self.frozen and not self.loan,'资产不可发')
        self.cycle+=1;t['cycle']=self.cycle;t['permit']=True

    def release(self,cid,valid=True):
        t=self.tasks[cid]
        require(self.commands[cid]['state']=='STARTED','状态不允许')
        require(t['permit'] and valid and self.safe and self.location=='held','无有效许可或不安全')
        self.location='pickup';self.loaded=False;self.release_count+=1

    def take(self,cid):
        require(self.location=='pickup' and self.owner==cid,'无本任务交付物')
        self.location='user';self.tasks[cid]['status']='TAKEN_LOCAL';self.commands[cid]['state']='DONE'

    def receive_issue_event(self,cid):
        require(self.tasks[cid]['status'] in ('TAKEN_LOCAL','APPLIED'),'没有取走证据')
        self.received.add(cid)

    def apply_issue(self,cid):
        require(self.online and cid in self.received,'尚无持久化事件')
        if cid in self.applied:return
        require(not self.loan,'资产存在其他借用')
        self.loan=cid;self.loans[cid]='ACTIVE';self.applied.add(cid)
        self.reservations.discard(cid);self.period_used+=1;self.tasks[cid]['status']='APPLIED'
        for rid,r in self.receipts.items():
            if r['issue']==cid and r['status']=='PENDING':self.apply_return(rid)

    def reset_channel(self):
        require(self.safe and self.owner and self.tasks[self.owner]['status'] in ('APPLIED','FAILED_NO_DELIVERY'),'缺安全或业务结论')
        require(self.location not in ('held','pickup'),'未清场')
        self.owner='';self.epoch+=1

    def return_open(self,rid,cid):
        require(self.online and rid not in self.return_sessions,'新归还需要在线新回执')
        require(cid in self.tasks,'缺原任务关联；真实不明场景应待核验')
        self.return_sessions[rid]=cid

    def return_transfer(self,rid,valid_identity=True,transferred=True,bin_ready=True):
        require(rid in self.return_sessions,'无柜端接管回执')
        require(bin_ready and transferred and valid_identity,'移交／身份条件不满足')
        if rid in self.receipts:return
        cid=self.return_sessions[rid]
        self.location='dirty' if self.online and cid in self.applied else 'isolation'
        self.clean=False;self.loaded=False;self.frozen=True
        self.receipts[rid]={'issue':cid,'cycle':self.tasks[cid]['cycle'],'status':'PENDING'}
        if self.online and cid in self.applied:self.apply_return(rid)

    def apply_return(self,rid):
        r=self.receipts[rid]
        if r['status']=='APPLIED':return
        cid=r['issue']
        require(self.online and cid in self.applied,'等待原借出证据')
        require(self.loan==cid and r['cycle']==self.tasks[cid]['cycle'],'不匹配原借用轮次')
        self.loans[cid]='RETURNED';self.loan='';self.frozen=False;r['status']='APPLIED'

    def wash(self):
        require(self.location in ('dirty','isolation'),'不在受控回收位置')
        self.location='inbound';self.clean=True

    def restock(self,manifest_match=True,identity_valid=True):
        require(self.location=='inbound' and self.clean,'未QC合格')
        require(not self.loan and not self.frozen,'原账未结或冻结')
        require(manifest_match and identity_valid,'装载身份差异')
        self.location='stock';self.loaded=True

    def crash_unknown(self,cid):
        self.tasks[cid]['status']='NEEDS_REVIEW';self.commands[cid]['state']='UNKNOWN';self.frozen=True

# 各反例要求被拒绝且无副作用，防止“报错但已经改账”。
def reject(m,call):
    before=deepcopy(m)
    try:call()
    except Refused:assert m==before;return
    raise AssertionError('该反例应被拒绝')

def held():
    m=Model();m.authorize('A');m.accept('A');m.start('A');return m

def taken(applied=True):
    m=held();m.permit('A');m.release('A');m.take('A');m.receive_issue_event('A')
    if applied:m.apply_issue('A')
    return m

checks=[]
def check(name,cases,fn):
    fn();checks.append({'name':name,'related_cases':cases,'result':'规则模型通过','real_device_result':'未执行'})

def full_cycle():
    m=taken();m.reset_channel();m.return_open('R1','A');m.return_transfer('R1');m.wash();m.restock()
    m.authorize('B');m.accept('B');m.start('B');m.permit('B');m.release('B');m.take('B');m.receive_issue_event('B');m.apply_issue('B')
    assert m.loan=='B' and m.tasks['B']['cycle']==2 and m.period_used==2
check('同资产两轮完整循环',['C01'],full_cycle)

def unauthorized():
    m=Model();reject(m,lambda:m.authorize('X',False));assert m.motion_starts==0 and not m.reservations
check('未授权无孤立预留',['C02'],unauthorized)

def quota():
    m=Model();m.authorize('A');reject(m,lambda:m.authorize('B'))
check('同额度主体第二请求被拒绝',['C03'],quota)

def channel():
    m=Model(reservation_limit=2);m.authorize('A');m.authorize('B');m.accept('A');reject(m,lambda:m.accept('B'))
check('同通道单执行所有者',['C04'],channel)

def duplicate():
    m=held();m=deepcopy(m);m.accept('A');m.start('A');assert m.motion_starts==1
check('重启保留日志后重复指令不再驱动',['C05'],duplicate)

def conflict():
    m=held();reject(m,lambda:m.accept('A','OTHER'))
check('同ID不同内容无副作用拒绝',['C06'],conflict)

def cancel_first():
    m=Model();m.authorize('A');m.cancel('A');assert m.accept('A')=='CANCELLED';reject(m,lambda:m.start('A'));assert not m.reservations
check('取消先完成拦截迟到指令',['C07'],cancel_first)

def start_first():
    m=held();reject(m,lambda:m.cancel('A'));assert 'A' in m.reservations
check('开始先完成不能取消退预留',['C08'],start_first)

def not_found():
    m=Model();m.authorize('A');assert 'A' not in m.commands and 'A' in m.reservations
    m.cancel('A');assert m.accept('A')=='CANCELLED'
check('查询未见不是取消证明',['C09'],not_found)

def offline_no_permit():
    m=held();m.online=False;reject(m,lambda:m.release('A'));assert m.location=='held'
check('无许可离线禁止公开释放',['C10'],offline_no_permit)

def offline_permit():
    m=held();m.permit('A');m.online=False;m.release('A');m.take('A');m.receive_issue_event('A');reject(m,lambda:m.authorize('B'))
    m.online=True;m.apply_issue('A');assert m.release_count==1
check('已有有效许可只完成原任务',['C11'],offline_permit)

def expired():
    m=held();m.permit('A');reject(m,lambda:m.release('A',False))
check('许可超期保持原物体',['C10'],expired)

def crash():
    m=held();m.crash_unknown('A');m=deepcopy(m);reject(m,lambda:m.start('A'));reject(m,lambda:m.cancel('A'));assert m.motion_starts==1
check('掉电结果未知不重新驱动',['C12'],crash)

def duplicate_event():
    m=taken();m.apply_issue('A');assert m.period_used==1 and m.loan=='A'
check('重复成功事件只记一次',['C13'],duplicate_event)

def ack_boundary():
    m=taken(False);assert 'A' in m.received and 'A' not in m.applied and not m.loan and 'A' in m.reservations
    reject(m,m.reset_channel)
check('已接收事件不等于业务已应用',['C13'],ack_boundary)

def unclaimed():
    m=held();m.permit('A');m.release('A');reject(m,lambda:m.cancel('A'));assert m.owner=='A' and 'A' in m.reservations
check('未取走不自动取消或解锁',['C14'],unclaimed)

def stuck_return():
    m=taken();m.return_open('R','A');reject(m,lambda:m.return_transfer('R',transferred=False));assert m.loan=='A'
check('只读身份未移交不得销账',['C17'],stuck_return)

def early_return():
    m=taken(False);m.return_open('R','A');m.return_transfer('R');assert m.frozen and m.receipts['R']['status']=='PENDING'
    m.apply_issue('A');assert m.loans['A']=='RETURNED' and not m.loan and m.period_used==1
check('归还先到等原借出证据',['C19'],early_return)

def old_return():
    m=taken();m.reset_channel();m.return_open('R','A');m.return_transfer('R');m.wash();m.restock()
    m.authorize('B');m.accept('B');m.start('B');m.permit('B');m.release('B');m.take('B');m.receive_issue_event('B');m.apply_issue('B')
    before=deepcopy(m);m.apply_return('R');assert m==before and m.loan=='B'
check('旧归还不结束新轮借用',['C20','C21'],old_return)

def invalid_return():
    m=taken();m.return_open('R','A');reject(m,lambda:m.return_transfer('R',valid_identity=False))
check('未知身份不自动销账',['C23'],invalid_return)

def full_bin():
    m=taken();m.return_open('R','A');reject(m,lambda:m.return_transfer('R',bin_ready=False))
check('无可用接收位置禁止转移',['C24'],full_bin)

def offline_new_return():
    m=taken();m.online=False;reject(m,lambda:m.return_open('R','A'))
check('不接受新离线归还',['C25'],offline_new_return)

def offline_old_return():
    m=taken();m.return_open('R','A');m.online=False;m.return_transfer('R');assert m.location=='isolation' and m.loan=='A'
    m.online=True;m.apply_return('R');assert not m.loan
check('已接管归还断网隔离待同步',['C26'],offline_old_return)

def unclosed_restock():
    m=taken(False);m.return_open('R','A');m.return_transfer('R');m.wash();reject(m,m.restock)
check('洗净原账未结禁止重新装载',['C27'],unclosed_restock)

def mismatched_manifest():
    m=taken();m.return_open('R','A');m.return_transfer('R');m.wash();reject(m,lambda:m.restock(False));reject(m,lambda:m.restock(identity_valid=False))
check('装载不符或身份失效不放行',['C28'],mismatched_manifest)

def old_versions():
    m=Model();m.authorize('A');reject(m,lambda:m.accept('A',assignment=0));reject(m,lambda:m.accept('A',epoch=0))
check('旧项目与旧通道版本禁止动作',['C30'],old_versions)

def period_count():
    m=taken();m.return_open('R','A');m.return_transfer('R');assert not m.loan and m.period_used==1
check('归还不返还周期使用次数',['C31'],period_count)

def unsafe_reset():
    m=taken();m.safe=False;reject(m,m.reset_channel);assert m.owner=='A'
check('业务完成但安全未恢复仍锁通道',['C32'],unsafe_reset)

out={'model_version':'V1.3','purpose':'文档规则反例检查，不是已实现系统或真机验收','checks_passed':len(checks),'checks':checks,'real_device_cases_total':32,'real_device_cases_executed':0,'limitations':['执行原子性、磁盘耐久、真实并发、网络协议均只是假设，需实现与实机验证','不模拟布料摩擦、条数、RFID湿读、夹困及传感器可靠性','不覆盖全部运营权限、SLA调度、审批、清洗与人员交接','不验证Liveo源码、数据库、部署或真实项目权限']}
Path(__file__).with_name('闭环规则模型结果.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print(json.dumps({'规则检查通过':len(checks),'真机用例执行':0,'真机计划用例':32},ensure_ascii=False))
