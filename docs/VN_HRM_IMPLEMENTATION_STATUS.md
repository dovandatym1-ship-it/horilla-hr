# Việt hóa Horilla HRM — kiểm kê code triển khai và tiêu chí bàn giao

**Cập nhật:** 18/10/2026 · **Baseline:** Horilla `2.0` tại `fad3c73f` · **Trạng thái:** Code đã push, CHƯA kiểm thử runtime/UAT và CHƯA merge.

## 1. Chuỗi PR và phạm vi
| PR | Base → Head | Những gì đang có | Chưa làm |
|---|---|---|---|
| #1 | 2.0 → feature/vietnam-hrm-foundation | BRD/SRS/UC, BR, dữ liệu và roadmap tiếng Việt | Không sửa code |
| #2 | 2.0 → feature/vn-i18n-foundation | Locale vi, múi giờ, VND mới, 294 chuỗi, format/test | Chưa dịch tất cả HTML/JS/PDF/Excel |
| #4 | feature/vn-i18n-foundation → feature/vn-dynamic-payroll-rules | Công thức động Decimal, lũy tiến theo bậc, effective date, approval, audit, tính thử Horilla và test | Chưa hook vào trả lương chính thức hoặc payline snapshot |
| #5 | feature/vn-dynamic-payroll-rules → feature/vn-hrm-domain | Hồ sơ pháp nhân, định danh mã hóa, người phụ thuộc, phụ lục, sổ phép, phân quyền, audit, admin hạn chế và test | Chưa kết nối bảng công, HĐ, phép, báo cáo hoặc khai thuế/BH vào luồng thực tế |

Merge theo thứ tự #2 → #4 → #5 sau khi có CI xanh/UAT. PR #1 là tài liệu độc lập, có thể review riêng.

## 2. Những chức năng đã có code
- **Rule engine:** AST sandbox, Decimal từ literal chính xác, reject unsafe syntax/function/unknown variables, `min/max/abs`, giá trị thập phân, tính lũy tiến theo JSON tier và kiểm tra ngưỡng.
- **Rule lifecycle:** công ty + mã + phiên bản, khoảng hiệu lực, nhập nháp, gửi duyệt, phê duyệt 2 người, ngừng áp dụng, tạo version, audit action; chặn sửa hàng loạt và công thức đã duyệt.
- **Preview adapter:** lấy các chỉ tiêu số từ payload `payroll_calculation` của Horilla đã được tính sẵn; kiểm tra nguồn biến, hiệu lực/role, SHA256 cấu hình+đầu vào, không lưu hay sửa Payslip/PayrollBatch.
- **Legal HR data:** mở rộng không phá `Employee`, `Company`, `Contract` gốc; CCCD/MST/BHXH ở dạng Fernet ciphertext + keyed HMAC; chỉ đọc khi có permission theo công ty và mục đích, lưu sự kiện truy cập không chứa plaintext.
- **Dependent/Contract/Leave:** hồ sơ người phụ thuộc và xác minh theo service; phụ lục có version, maker/checker, date overlap; sổ phép Decimal/idempotency/append-only.

## 3. Bắt buộc cấu hình để dùng an toàn
Cấu hình riêng trên server/app secrets, không commit key:
```dotenv
LANGUAGE_CODE=vi
TIME_ZONE=Asia/Ho_Chi_Minh
DEFAULT_CURRENCY_SYMBOL=₫
VN_PII_FERNET_KEY=<generated Fernet key from your secrets manager>
```
Tạo key bằng lệnh `python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'`. Sao lưu khóa **riêng** với database, thiết kế xoay khóa và chiến lược khôi phục trước khi nhập CCCD thật. Thiếu khóa, hệ thống từ chối mã hóa và đọc dữ liệu định danh thay vì ghi plaintext.

## 4. Danh sách kiểm chứng phải chạy ngoài GitHub connector
```bash
python manage.py check
python manage.py check --fail-level WARNING --tag horilla.tenancy
python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py test vn_payroll.tests vn_hrm.tests horilla.tests.test_vietnam_localization payroll.tests.test_vietnam_currency
make test-cov
ruff check .
black --check horilla/settings
```
Phải ghi **PASS/FAIL/NOT RUN** theo log thật. GitHub fork hiện chưa có workflow run trong các kết quả truy vấn; **không tuyên bố đã PASS**.

## 5. Các miền nghiệp vụ CHƯA hoàn thành
| Nhóm | Việc còn làm trước production |
|---|---|
| Việt hóa UX/UI | Dịch hàng nghìn gettext còn lại, JS custom, form, notification, email, PDF/Excel, datagrid và kiểm thử responsive |
| Hồ sơ HR | UI sử dụng được bởi HR theo vai trò (không chỉ superuser), hành chính tỉnh/xã theo thời gian và lịch sử điều chuyển |
| HĐLĐ | Đưa phụ lục approved vào lookup lương theo ngày hiệu lực; soát loại HĐ, chấm dứt, lưu trữ |
| Công–Phép–OT | Đồng bộ lịch/ca, nghỉ/OT được duyệt vào payroll; quy trình chỉnh công/chốt công/ledger không đúp |
| Payroll | Production adapter, canonical inputs, immutable payline snapshot, Decimal across Horilla FloatFields, benchmark và golden tests |
| Thuế/BH | Bộ luật theo thời điểm hiệu lực, nhóm lao động, trần, nền đóng, ưu đãi/ngoại lệ; thẩm định với Pháp chế/Kế toán |
| Báo cáo | `vn_reports`, tờ trình, tổng hợp BH/TNCN, báo cáo ngân hàng, export bảo vệ dữ liệu |
| Triển khai | Backup/restore, key rotation, monitoring, DPIA nếu thuộc trường hợp áp dụng, CI/UAT và pilot |

Không dùng chức năng cấu hình/tính thử để khẳng định phần mềm tuân thủ đầy đủ pháp luật hoặc tự động chi trả. Tình huống ảnh hưởng tiền thật phải do HR/Payroll/Pháp chế duyệt và đối soát trước.

## 6. Quy tắc phát hành
**No-Go** nếu còn trường hợp thiếu quyền, lộ PII, logic chi trả chưa đối soát, migration drift, không thể restore hoặc rule thời điểm hiệu lực chưa được phê duyệt. Không merge trực tiếp vào `2.0` hoặc đánh dấu UAT PASS khi chưa có bằng chứng chạy.


---

## 7. Cập nhật Phase 2 — PR #6 (18/10/2026)

Phần kiểm kê ở các mục trên phản ánh trạng thái PR #5. PR #6 tiếp tục triển khai code trên nhánh `feature/vn-hrm-payroll-reconciliation`, **chưa merge**, chỉ dùng để đối soát trước chi trả:

- `vn_hrm/payroll_sources.py`: lookup phụ lục `approved` theo ngày, snapshot số ngày nghỉ duyệt/OT đã duyệt/chấm công validated/sổ phép; từ chối phụ lục thay đổi hoặc nghỉ phép giao kỳ không thể phân bổ an toàn.
- `vn_payroll/decimal_tools.py`: phép tính Decimal của VND, tỷ lệ và trần cấu hình; KHÔNG khôi phục lỗi đã phát sinh từ core FloatField.
- `vn_payroll/golden_cases.py`: độc lập so khớp ít nhất ba test vectors cho rule có hiệu lực đã được duyệt; yêu cầu căn cứ pháp lý với danh mục tax/insurance, không tự xác nhận tính hợp pháp.
- `vn_hrm/reports.py`: Gross/Net aggregate và CSV không chứa PII, chỉ sử dụng các phiếu confirmed/paid và kiểm tra phạm vi công ty cùng quyền `view_payslip`.
- `scripts/audit_vi_locale.py`: kiểm kê gettext tiếng Việt; `docs/VN_HRM_UAT_MATRIX.md`: danh sách kịch bản UAT phải nghiệm thu.
- `.github/workflows/vn-hrm-integrity.yml`: CI PostgreSQL, Django system check, migration drift, migration và test.

| Hạng mục | Kết quả hiện có | Chưa đủ để đánh dấu hoàn tất |
|---|---|---|
| Việt hóa 100% | Nền tảng gettext + công cụ đo | Còn hàng nghìn chuỗi và nhiều UI/JS/Email/PDF/Excel chưa thẩm tra |
| Phụ lục → tính lương | Lookup phụ lục approved và preview | Chưa thay thế pipeline phiếu lương chính thức |
| Phép/công/OT → Payroll | Approved input và snapshot read-only | Chưa xử lý tất cả giao kỳ/khóa sổ/payline |
| Thay FloatField tiền lõi | Decimal boundary và thử nghiệm độc lập | Chưa migrate toàn bộ FloatField và thuật toán sử dụng float |
| Báo cáo Việt Nam | Tổng hợp nội bộ Gross/Net + CSV | Chưa phải tờ khai TNCN/BHXH/bảng ngân hàng |
| Thuế/BH độc lập | Runner golden case, rule động | Chưa có bộ luật chuẩn theo hiệu lực được thẩm định/đối soát |
| Django/migration/CI/UAT | CI được tạo/kích hoạt | PASS/FAIL phải dựa trên log thực; UAT chưa thực hiện |

**Quyết định phát hành: NO-GO cho production payroll/chi trả** cho đến khi các mục còn lại đã kiểm chứng. PR #6 ở trạng thái draft để tránh hiểu sai về việc hoàn thành nghiệm thu.
