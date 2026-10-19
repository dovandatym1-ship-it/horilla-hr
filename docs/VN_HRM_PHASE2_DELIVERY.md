# Horilla Việt Nam — đối soát nguồn HRM / Payroll (Phase 2)

**Ngày:** 18/10/2026. **Trạng thái:** Mã nguồn đã bổ sung; chưa chứng minh runtime Django, CI xanh, UAT hoặc sản phẩm đủ điều kiện chi trả.

## Phạm vi đã code
- `vn_hrm.payroll_sources.effective_contract_wage`: lấy lương phụ lục *approved* theo ngày, fallback nguồn Horilla legacy; khóa phạm vi pháp nhân, kiểm tra hiệu lực hợp đồng, không chọn nhiều bản trùng.
- `vn_hrm.payroll_sources.period_sources`: đọc thông tin phép đã duyệt, OT đã duyệt **và chấm công hợp lệ**, số dư nhật ký phép, và mức lương phụ lục ra các biến Decimal chuẩn hóa. Từ chối nghỉ giao kỳ lương và phụ lục đổi mức giữa kỳ (phải phân bổ/tách kỳ, không tính ước lượng). Không nhân đôi trừ phép vào payroll.
- `vn_hrm.payroll_sources.preview_with_hrm_sources`: dùng đúng nguồn nêu trên cho rule được duyệt của `vn_payroll.bridge`, kèm fingerprint SHA256; **chỉ read-only, không ghi Payslip hoặc phát lệnh chi trả**.
- `vn_payroll.decimal_tools`: Decimal nghiêm ngặt, làm tròn HALF_UP VND, hàm tỷ lệ/cơ sở đóng/trần cấu hình động, không hardcode pháp luật.
- `vn_hrm.reports.payroll_period_summary`: tổng hợp Gross/Net và số phiếu đã xác nhận/chi trả theo pháp nhân, không xuất hồ sơ định danh hoặc tên nhân viên, từ nguồn FloatField Horilla nên vẫn có giới hạn về độ chính xác.
- Bộ kiểm thử độc lập cho Decimal và nghiệp vụ hợp đồng; workflow GitHub Actions dùng PostgreSQL, system check, migration drift, migrate và chạy test hiện hữu.
  
## Chưa đạt tiêu chí hoàn tất của yêu cầu
| Hạng mục | Trạng thái trung thực / kiểm chứng còn thiếu |
|---|---|
| Việt hóa 100% | Chưa đạt. Nền tảng mới có 294 gettext vi ở PR #2; vẫn còn HTML/JS, email, thông báo, PDF và report. |
| Phụ lục → tính lương | Đã kết nối nguồn vào **preview**; chưa thay engine sản xuất và snapshot payline. |
| Sổ phép/chấm công/OT → Payroll | Đã có input read-only được kiểm tra quyền và duyệt; chưa hook trả lương, xử lý kỳ giao nhau và chống trùng production. |
| FloatField tiền tệ | Chưa thay trường model và toán tử lõi; lớp tính Decimal bên cạnh không loại bỏ sai số phát sinh trước đó. |
| Báo cáo chuyên biệt | Đã có tổng hợp nội bộ tối thiểu, chưa có bảng mẫu TNCN, BHXH, ngân hàng, báo cáo cơ quan nhà nước. |
| Thuế & bảo hiểm | Có công thức tỷ lệ Decimal có trần do người cấu hình; chưa có bộ dữ liệu luật theo thời gian, hồ sơ đối chiếu chuyên gia hoặc golden UAT chính thức. |
| Django/migration/CI/UAT | Đã thêm CI workflow; trạng thái là **NOT RUN** cho đến khi có log chạy. UAT cần nhân sự và kế toán xác nhận độc lập. |

## Điều kiện an toàn
Phải có rule version được duyệt riêng theo pháp nhân và ngày hiệu lực, mapping loại thu nhập/nền đóng rõ, backup/restore kiểm tra được, key Fernet riêng, quyền truy cập tách vai trò, chống chạy lặp và đối soát bảng lương trước mọi cơ chế payline/write. Không sử dụng dữ liệu demo dưới danh nghĩa tham số thuế/bảo hiểm Việt Nam hiện hành.

## Kiểm tra
```sh
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --noinput
python manage.py test vn_payroll.tests vn_hrm.tests --noinput
```

**Không merge hoặc bật chi trả** chỉ dựa trên unit tests; UAT, thẩm định quy tắc pháp luật theo ngày hiệu lực và regression payroll vẫn bắt buộc.
