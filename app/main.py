from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Mini Finance System")

# 模拟数据库：当前应付余额
current_payable_balance = 1000.0
# 模拟数据库：凭证列表
vouchers = []

class Voucher(BaseModel):
    debit_account: str    # 借方科目
    credit_account: str   # 贷方科目
    amount: float         # 金额
    maker: str            # 制单人
    checker: str          # 审核人

class Payment(BaseModel):
    amount: float

@app.post("/api/voucher")
def create_voucher(v: Voucher):
    # 规则1：借贷必相等（这里模拟输入的是一个复合凭证，或者校验金额）
    if v.amount <= 0:
        raise HTTPException(status_code=400, detail="金额必须大于0")
    
    # 规则2：制单人与审核人不能为同一人（财务合规）
    if v.maker == v.checker:
        raise HTTPException(status_code=403, detail="制单人与审核人不能为同一人")
    
    vouchers.append(v)
    return {"status": "success", "message": "凭证保存成功"}

@app.post("/api/payment")
def make_payment(p: Payment):
    global current_payable_balance
    # 规则3：付款金额不能超过当前应付余额
    if p.amount > current_payable_balance:
        raise HTTPException(status_code=400, detail="付款金额超过应付余额")
    
    current_payable_balance -= p.amount
    return {"status": "success", "current_balance": current_payable_balance}

@app.get("/api/balance")
def get_balance():
    return {"current_payable_balance": current_payable_balance}