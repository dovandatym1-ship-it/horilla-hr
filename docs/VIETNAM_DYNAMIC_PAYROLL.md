# Công thức động tính lương Việt Nam (giai đoạn cấu hình)

> **CẬP NHẬT CODE NGÀY 18/10/2026:** Đã bổ sung sửa lỗi Decimal literal, kiểm tra cú pháp, scope theo công ty, phê duyệt tách người lập/người duyệt, từ chối hiệu lực chồng chéo, khóa rule đã duyệt, tạo phiên bản mới và bộ tính lũy tiến tùy chỉnh. Có adapter `vn_payroll.bridge.preview_from_horilla` chỉ để **tính thử trên kết quả payroll Horilla**, không làm thay đổi phiếu lương/giải ngân. Các test mới đã viết nhưng chưa được xác nhận chạy bởi CI.


Đây là **code thật** cho bộ công thức tùy chỉnh, không phải cam kết đã tích hợp đầy đủ luật thuế, BHXH hoặc thanh toán.

## Có thể làm ngay
- Khai báo biểu thức số học: `gross - employee_insurance - pit - advance`, `base_hourly * ot_hours * multiplier`, `max(0, gross - deduction)`.
- Khai báo tên biến đầu vào, loại công thức, pháp nhân, thời gian hiệu lực, phiên bản và số chữ số thập phân.
- Xem/lưu bản nháp công thức trong **Django Admin** theo quyền superuser; gửi duyệt, phê duyệt và ngừng áp dụng qua admin actions sử dụng dịch vụ có kiểm tra quyền, phân tách người lập/người duyệt. Các tác vụ ngoài Admin phải sử dụng dịch vụ trong `vn_payroll.services`.
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
- Đã có workflow gửi duyệt/phê duyệt/ngừng qua service/admin, nhưng **chưa có nhật ký phê duyệt riêng, snapshot payline được lưu DB, API màn hình nhân sự chuyên biệt hoặc tích hợp sản xuất**. Các cách ghi trực tiếp vào DB ngoài Django vẫn cần chính sách DB/giám sát và không được coi là đường nghiệp vụ hợp lệ.
- Rule có thể là một biểu thức số học hoặc bộ bậc lũy tiến `calculation_kind=progressive` với danh sách `{up_to, rate_percent}`. Cấu hình bậc/tỷ lệ KHÔNG phải tự động khẳng định đúng pháp luật; doanh nghiệp phải cung cấp thu nhập tính thuế hợp lệ, rule version, mốc hiệu lực và căn cứ duyệt.
- Tên biến phải nằm trong danh sách `variables`; không hỗ trợ truy cập hệ thống/tệp/SQL hoặc hàm Python.
- Để thay đổi rule đã áp dụng, tạo `version` mới; không sửa đè rule cũ.

## Chạy kiểm tra
```bash
python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py test vn_payroll.tests
```

Lưu ý: **Chưa chạy bộ kiểm thử này trên GitHub CI ở thời điểm commit**.


## Ví dụ cấu hình theo bậc động (minh họa thuật toán)
```python
from vn_payroll.brackets import progressive_amount

brackets = [
    {"up_to": "10000000", "rate_percent": "5"},
    {"up_to": "30000000", "rate_percent": "10"},
    {"up_to": "60000000", "rate_percent": "20"},
    {"up_to": None, "rate_percent": "30"},
]
print(progressive_amount("35000000", brackets))
```
Các ngưỡng ví dụ chỉ để minh họa engine; **không sử dụng làm bộ quy tắc pháp luật nếu chưa được xác minh**.

## Lựa chọn công thức theo ngày hiệu lực và tính thử trên Horilla
```python
from datetime import date
from vn_payroll.bridge import preview_from_horilla

# payroll_data là payload *đã tính sẵn* từ engine hiện có;
# actor phải có quyền preview_formularule và phạm vi công ty.
preview = preview_from_horilla(
    company_id=1,
    code="NET_CHECK",
    effective_on=date(2026, 10, 18),
    actor=authorized_user,
    payroll_data={"gross_pay": 18000000, "total_deductions": 1500000},
)
```
Hàm trả kết quả, version và mã SHA-256 đối soát; không ghi đè `Payslip`, `PayrollBatch`, hợp đồng hoặc lương đã thanh toán.

**Không dùng rule preview để tự động trả lương.** Cần thêm dòng chi tiết payline, sổ audit bất biến, nguồn dữ liệu nhân sự có hiệu lực, phân loại khoản chịu thuế/BH, kiểm thử golden độc lập và duyệt phát hành trước khi bật production.
