# HRM Việt Nam — triển khai mã nguồn và công thức động

**Nhánh:** `feature/vn-dynamic-hrm` (dựa trên `feature/vn-i18n-foundation`); **trạng thái:** bản triển khai nền, **chưa nối vào bảng lương đã trả của Horilla**. Không sử dụng để tính lương/khấu trừ BH/thuế chính thức khi chưa đối soát và ký duyệt.

## 1. Đã triển khai bằng code
| Module | Mã nguồn | Chức năng thực tế | Chưa tích hợp |
|---|---|---|---|
| Công thức lương động | `vn_payroll/engine.py` | Safe AST evaluator, Decimal, biểu thức điều kiện, min/max/abs/round_vnd | Chưa ghi Payslip gốc |
| Quy tắc theo công ty | `vn_payroll/models.py` | RuleSet theo company/code/version/effective dates, rule lines theo thứ tự | Không tự động xác định mọi trường hợp pháp lý |
| Quản trị công thức | `vn_payroll/admin.py` | CRUD bản Nháp, chuyển Chờ duyệt, maker/checker, tính thử bằng JSON | Chưa có HR staff UI phân quyền từng pháp nhân |
| Kiểm thử bắt buộc khi duyệt | `VNRuleSet.golden_cases` | Đối soát input/expected do Kế toán cung cấp, không đúng thì chặn duyệt | Không thay thế kiểm toán kế toán độc lập |
| Hồ sơ nhân viên | `vn_hrm/models.py` | CCCD/MST/BHXH chỉ lưu 4 số cuối và opaque vault reference, cư trú | Chưa kết nối kho lưu PII mã hóa |
| Người phụ thuộc | `VNDependent` | Loại quan hệ, hiệu lực, trạng thái xác minh | Chưa tự chuyển sang khấu trừ PIT |
| Phụ lục HĐ | `VNContractAmendment` | Lương tháng VND Decimal, hiệu lực, workflow duyệt | Chưa thay `payroll.Contract.wage` |
| Điều chỉnh công | `VNAttendanceCorrection` | Yêu cầu, người duyệt, dấu audit, hạn chế sửa sau duyệt | Chưa cập nhật `Attendance` / `WorkRecord` |
| Ledger phép | `VNLeaveLedgerEntry` | Giao dịch tăng/giảm có khóa chống gửi trùng và không sửa từ UI | Chưa đồng bộ `AvailableLeave` |
| Kiểm thử | `vn_payroll/tests/`, `vn_hrm/tests/` | Unit/DB regression được viết | Phải chạy CI/PostgreSQL trước merge |

Các model mới dùng migration `vn_payroll/migrations/0001_initial.py` và `vn_hrm/migrations/0001_initial.py`; không ALTER bảng gốc Horilla.

## 2. Cấu hình công thức trên trang quản trị
Đăng nhập bằng **Django superuser** tại `/admin/` → **Công thức tính lương Việt Nam** → **Thêm bộ công thức**. Chọn Công ty, mã bộ (ví dụ `monthly_demo`), phiên bản, ngày hiệu lực. Điền `input_names`, `parameters`, `golden_cases`, các dòng công thức và căn cứ văn bản/quy chế. Hệ thống chỉ cho chỉnh sửa ở trạng thái Nháp. Sau khi có dòng công thức, chuyển **Chờ duyệt**. Một tài khoản quản trị khác với người lập phê duyệt. Nếu formula dùng biến chưa khai báo hoặc Golden Case lệch kết quả, **không cho phê duyệt**.

Tại màn hình danh sách → **Tính thử** → nhập dữ liệu JSON giả lập. Không nhập dữ liệu lương thật: ứng dụng không lưu input của trang tính thử vào DB, nhưng nhà vận hành phải kiểm soát reverse-proxy/access/error logs.

### 2.1. Ví dụ minh họa — KHÔNG phải quy định pháp luật
**input_names**
```json
["salary", "paid_days", "standard_days", "ot_hours", "hour_rate"]
```

**parameters** (tỷ lệ giả định; Kế toán tự thay bằng thông số có phê duyệt)
```json
{
  "demo_insurance_rate": "0.10",
  "demo_ot_multiplier": "1.50"
}
```

**Các dòng tính (đúng thứ tự)**
| Position | Code | Category | Expression |
|---|---|---|---|
| 10 | `base` | earning | `round_vnd(salary * paid_days / standard_days)` |
| 20 | `ot` | earning | `round_vnd(ot_hours * hour_rate * demo_ot_multiplier)` |
| 30 | `gross` | subtotal | `base + ot` |
| 40 | `insurance` | insurance_employee | `round_vnd(gross * demo_insurance_rate)` |
| 50 | `net` | net | `gross - insurance` |

**golden_cases** (đối soát giả định 20/20 ngày, hai giờ OT)
```json
[
  {
    "inputs": {
      "salary": "10000000",
      "paid_days": "20",
      "standard_days": "20",
      "ot_hours": "2",
      "hour_rate": "50000"
    },
    "expected": {
      "base": "10000000",
      "ot": "150000",
      "gross": "10150000",
      "insurance": "1015000",
      "net": "9135000"
    }
  }
]
```

Khi thay tỷ lệ, không sửa bộ đã duyệt. Tạo phiên bản mới có hiệu lực, bộ test mới, nguồn căn cứ và người phê duyệt khác. Các kỳ đã Paid giữ snapshot cũ. Phần kết nối snapshot vào Horilla Payroll còn phải được triển khai và UAT trước production.

### 2.2. Ngôn ngữ biểu thức an toàn
Hỗ trợ số/nguyên/Decimal, tên biến viết thường, `+`, `-`, `*`, `/`, `<`, `<=`, `>`, `>=`, `==`, `!=`, `and`, `or`, biểu thức `X if condition else Y`, `min(...)`, `max(...)`, `abs(...)`, `round_vnd(...)`. Không hỗ trợ `eval`, `exec`, `import`, attribute access, indexing, comprehension, `pow`, vòng lặp, function tự viết, network access. Tối đa 700 ký tự/100 AST node/20 lớp lồng, giới hạn biên trị số để tránh lỗi tính toán. Dùng số/giá trị tham số ở dạng **chuỗi số thập phân** (ví dụ `"0.08"`) để không nhập sai do số chấm động JSON.

Trước khi duyệt, hệ thống kiểm tra tên biến, thứ tự phụ thuộc, cú pháp AST, thiếu biến đầu vào, đối chiếu Golden Cases. Để dùng trên bảng lương chính thức còn cần rule pack theo đối tượng NLĐ/pháp nhân, test ranh giới thuế, BH và chốt chính sách phê duyệt.

## 3. Triển khai và kiểm thử
```bash
git checkout feature/vn-dynamic-hrm
python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py check
python manage.py test vn_payroll.tests vn_hrm.tests
```

Hoặc `docker compose up --build -d` theo hướng dẫn repo, hệ thống sẽ áp migration. Với triển khai production, **backup DB/media trước khi migrate**, diễn tập restore, review migration và chạy bộ test trên PostgreSQL giống production.

## 4. Điều kiện để gọi là triển khai xong toàn bộ HRM
- Giao diện các module Horilla (menu, form, script, PDF, Excel) được dịch đủ, kiểm thử ngôn ngữ trên trình duyệt.
- Hệ thống lưu CCCD/MST/BHXH có cơ chế mã hóa/vault được triển khai thực tế, có quyền dữ liệu theo vai trò/pháp nhân.
- Hồ sơ pháp lý, phụ lục HĐ và người phụ thuộc được kết nối với quy trình HR gốc và lịch sử điều chuyển.
- Lớp công/phép cập nhật kết quả Horilla có lock kỳ, đối soát và rollback/compensating events.
- Tính lương chính thức nhận dữ liệu công/HĐ/thu nhập đã chốt, dùng đúng rule version theo kỳ, xuất Payslip có source hash; Paid immutable.
- Golden payroll 2026 đủ đối tượng, luật, ngoại lệ; người HR/Kế toán/Pháp chế ký duyệt, kiểm toán đủ bằng chứng.
- CI, security, UAT và pilot đạt.

**Những điều trên chưa thể khẳng định đã hoàn tất chỉ bằng việc thêm engine và mô hình dữ liệu.** Tài liệu này là báo cáo phạm vi rõ ràng nhằm tránh đưa hệ thống chưa hoàn thiện vào vận hành thật.
