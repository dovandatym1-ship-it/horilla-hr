# Kịch bản UAT Việt Nam — bắt buộc xác minh thủ công

**Chưa thực thi:** danh mục này không phải biên bản nghiệm thu. HR, C&B, Kế toán, Pháp chế và QA phải ký xác nhận kết quả thực tế, ngày chạy, phiên bản rule, log test, dữ liệu giả lập và người duyệt.

| Nhóm | Kịch bản tối thiểu | Kỳ vọng |
|---|---|---|
| Việt hóa | Login, menu, form, lỗi validate, toast, bảng lọc, email, PDF, Excel, mobile | Không còn chuỗi tiếng Anh ở phạm vi nghiệm thu |
| Định dạng | VND, số âm, 0, ngày 29/02, dd/MM/yyyy, múi giờ | Chính xác và không phá dữ liệu lịch sử |
| Phụ lục | Nháp/chờ duyệt/đã duyệt, khác người phê duyệt, version, chồng ngày, giữa kỳ | Khoá sai quyền; chọn đúng version hoặc yêu cầu tách kỳ |
| Bảng công | Ca đêm, công thiếu, yêu cầu chỉnh, chấm công chưa xác thực | Không lấy dữ liệu chưa chốt vào kỳ lương |
| OT | Ngày thường/ngày nghỉ/lễ, bù, đảo phê duyệt, OT trùng | Không tính lại hoặc lạm cộng giờ |
| Phép | Nửa ngày, giao tháng, giao năm, hoàn/trừ bù, tồn đầu kỳ | Không trừ đúp; giao kỳ bị khóa để phân bổ |
| Lương | Gross/net, CTC Down, hourly, daily, proration, người nghỉ việc | Đối chiếu 100% với bảng tính độc lập |
| Độ chính xác | Decimal 0.1+0.2, rounding VND, số lớn, thay FloatField legacy | Không có sai số, không mất lịch sử |
| Thuế | Nhiều bậc, giảm trừ, người phụ thuộc, cư trú/không cư trú, luật đổi giữa kỳ | Căn cứ và version được duyệt, có golden test |
| BHXH/BHYT/BHTN | Trần, vùng, loại HĐ, ngoại lệ, quỹ NLĐ/DN, mốc hiệu lực | So khớp phép tính và bảng tính độc lập |
| Báo cáo | Chốt bảng lương, bảng ngân hàng, hồ sơ BH, TNCN, xuất CSV/Excel | Số tổng khớp payline, truy cập có quyền, không lộ PII |
| Bảo mật | Vai trò công ty khác, lộ mã định danh, audit, key rotation, restore | Fail-closed, logs không chứa plaintext |
| Vận hành | Fresh install + migration, rollback, backup/restore, CI, load test, concurrency | Bằng chứng PASS cho phiên bản được bàn giao |

## Gate phát hành
1. Chạy CI trên PostgreSQL và lưu kết quả PASS, không tự suy diễn từ việc đã có workflow.
2. Đối chiếu đầu ra payroll của 3 kỳ độc lập với bảng tính HR/C&B và Kế toán.
3. Xác thực bộ tham số pháp luật, hiệu lực, trường hợp ngoại lệ bởi người có trách nhiệm.
4. Đánh giá bảo mật dữ liệu định danh và quyền theo pháp nhân; kiểm tra khôi phục khóa.
5. Chưa đạt bất kỳ gate bắt buộc nào thì giữ ở chế độ preview, không tự phát lệnh thanh toán.
