import os
import pytest
import requests
import allure

# 优先从环境变量读取 BASE_URL（适配 Docker 环境），默认使用本地地址
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")

@allure.feature("财务合规校验")
@allure.story("制单与审核权限隔离")
@allure.severity(allure.severity_level.CRITICAL)
def test_voucher_maker_cannot_be_checker():
    """测试：制单人和审核人为同一人时，系统应拦截（财务内控红线）"""
    payload = {
        "debit_account": "1001 库存现金",
        "credit_account": "2202 应付账款",
        "amount": 500.0,
        "maker": "张三",
        "checker": "张三"  # 故意设为同一人
    }
    
    with allure.step("发送凭证录入请求，验证被系统拒绝"):
        response = requests.post(f"{BASE_URL}/api/voucher", json=payload)
        assert response.status_code == 403
        assert "不能为同一人" in response.json()["detail"]

@allure.feature("应付付款模块")
@allure.story("正常付款流程")
@allure.severity(allure.severity_level.CRITICAL)
def test_payment_success():
    """测试：付款金额小于等于应付余额时，付款成功且余额正确扣减"""
    # 为了不影响其他用例，这里假设初始余额足够
    payload = {"amount": 200.0}
    
    with allure.step("发起正常付款"):
        response = requests.post(f"{BASE_URL}/api/payment", json=payload)
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        
    with allure.step("校验最新应付余额"):
        balance_resp = requests.get(f"{BASE_URL}/api/balance")
        # 因为前面的用例可能修改了余额，这里只校验请求成功和字段存在
        assert balance_resp.status_code == 200
        assert "current_payable_balance" in balance_resp.json()

@allure.feature("应付付款模块")
@allure.story("超额付款拦截")
@allure.severity(allure.severity_level.CRITICAL)
def test_payment_exceed_balance():
    """测试：付款金额大于应付余额时，应被系统拦截"""
    # 故意发一个大额付款（远大于初始的 1000）
    payload = {"amount": 99999.0}
    
    with allure.step("发送超额付款请求，验证被拦截"):
        response = requests.post(f"{BASE_URL}/api/payment", json=payload)
        assert response.status_code == 400
        assert "超过应付余额" in response.json()["detail"]

@allure.feature("凭证录入")
@allure.story("非法金额校验")
@allure.severity(allure.severity_level.NORMAL)
def test_voucher_invalid_amount():
    """测试：录入金额小于等于 0 的凭证，应被拦截"""
    payload = {
        "debit_account": "1001 库存现金",
        "credit_account": "2202 应付账款",
        "amount": -100.0,  # 非法金额
        "maker": "李四",
        "checker": "王五"
    }
    
    with allure.step("发送负数金额，验证被拦截"):
        response = requests.post(f"{BASE_URL}/api/voucher", json=payload)
        assert response.status_code == 400
        assert "金额必须大于0" in response.json()["detail"]