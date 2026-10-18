# Công thức động tính lương Việt Nam (giai đoạn cấu hình)

Đây là **code thật** cho bộ công thức tùy chỉnh, không phải cam kết đã tích hợp đầy đủ luật thuế, BHXH hoặc thanh toán.

## Có thể làm ngay
- Khai báo biểu thức số học: `gross - employee_insurance - pit - advance`, `base_hourly * ot_hours * multiplier`, `max(0, gross - deduction)`.
- Khai báo tên biến đầu vào, loại công thức, pháp nhân, thời gian hiệu lực, phiên bản và số chữ số thập phân.
- Xem/lưu bản nháp công thức trong **Django Admin** theo quyền superuser, không cho phép người dùng thường truy cập công thức thuộc pháp nhân khác.
- Tính thử qua `FormulaRule.calculate_preview({...})` với `Decimal`; công thức bị hạn chế cú pháp, không thể chạy Python tùy ý.

## Mẫu thao tác Python
```python
from vn_payroll.expression import evaluate

net = evaluate(
    "gross - employee_insurance - pit - advance",
    {
        "gross": "25000000",
        "employee_insurance": "2000000",
        "pit": "1000000",
        "advance": "500000",
    },
)
# Decimal('21500000')
```

## Tại sao không auto-hook vào bảng lương?
Tính lương production đòi hỏi xác thực nguồn công/hợp đồng, phân loại các khoản lương và quyền thuế, phiên bản hiệu lực, phê duyệt, snapshot, kiểm thử độc lập. Chỉ chọn `approved` trên rule chưa đủ để chạy thật; việc đưa vào payroll chính thức phải là PR tích hợp riêng có kiểm soát và test đối soát. Không thiết lập tỷ lệ bảo hiểm/thuế mặc định khi chưa có xác minh.

## Hạn chế hiện tại
- Django Admin là nơi *chỉnh cấu hình*, không phải UI HR chuyên biệt.
- Chưa có phê duyệt bằng workflow, ledger/snapshot payline, API cấu hình hoặc tích hợp run của Horilla.
- Rule đang ở mức một biểu thức; biểu thuế nhiều bậc cần biểu diễn thành nhiều quy tắc hoặc engine bracket chuyên biệt; doanh nghiệp phải cung cấp biến tính thuế hợp lệ.
- Tên biến phải nằm trong danh sách `variables`; không hỗ trợ truy cập hệ thống/tệp/SQL hoặc hàm Python.
- Để thay đổi rule đã áp dụng, tạo `version` mới; không sửa đè rule cũ.

## Chạy kiểm tra
```bash
python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py test vn_payroll.tests.test_expression vn_payroll.tests.test_rules
```

Lưu ý: **Chưa chạy bộ kiểm thử này trên GitHub CI ở thời điểm commit**.
