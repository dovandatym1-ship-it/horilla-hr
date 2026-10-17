# VN-HRM | Chuẩn hóa giao diện, hiển thị và thông điệp tiếng Việt
**Mã:** VNHRM-UI-09 · **Phiên bản:** 1.0 · **Trạng thái:** Đặc tả giao diện TO-BE, chưa triển khai frontend · **Ngày:** 17/10/2026

## 1. Định hướng UX/UI
Tận dụng giao diện/Design System Horilla, không tự ý đổi màu, spacing, pattern action khi chưa có quyết định thiết kế. Mỗi màn hình có header (breadcrumb, tiêu đề, mô tả), thanh tìm kiếm và bộ lọc, bảng dữ liệu, thao tác chính, menu tác vụ hàng, phân trang, empty/error/loading/success state; bố trí hành động chính nhất quán; ẩn hoặc vô hiệu chức năng người dùng không có quyền theo policy và luôn kiểm tra lại tại server. Văn bản cần rõ chủ thể, kết quả, đơn vị, thời gian và ảnh hưởng của thao tác.

**Chuẩn chung:** dùng nhãn tiếng Việt có dấu; `dd/MM/yyyy`; HH:mm (24 giờ); VND `1.234.567 ₫`; thời gian nội bộ UTC, hiển thị Asia/Ho_Chi_Minh; số liệu lương căn phải, mã căn trái, trạng thái không chỉ biểu đạt bằng màu. Phân biệt “Xóa” với “Lưu trữ”; “Hủy” trên modal với “Hủy đơn” có hiệu lực nghiệp vụ.

## 2. Menu điều hướng chuẩn cho MVP
- Tổng quan
- Tổ chức: Pháp nhân, Phòng ban, Chức danh, Địa điểm làm việc, Ca và lịch làm việc
- Nhân sự: Danh sách nhân viên, Hồ sơ nhân viên, Người phụ thuộc, Tài liệu nhân sự
- Hợp đồng: Hợp đồng lao động, Phụ lục, Cảnh báo hết hạn
- Chấm công: Chấm công hằng ngày, Yêu cầu điều chỉnh, Làm thêm giờ, Bảng công tháng, Chốt bảng công
- Nghỉ phép: Số dư phép, Đơn nghỉ, Quy định nghỉ và ngày lễ
- Tiền lương: Thành phần lương, Kỳ lương, Bảng lương, Phiếu lương, Điều chỉnh truy lĩnh/truy thu
- Thuế và bảo hiểm: Hồ sơ thuế, Người phụ thuộc, Danh sách tham gia BH, Bộ quy tắc theo hiệu lực
- Báo cáo: Nhân sự, Công, Nghỉ, Lương, Bảo hiểm, Thuế, Đối soát ngân hàng
- Quản trị: Người dùng, Vai trò, Phạm vi dữ liệu, Nhật ký hệ thống, Cấu hình chính sách

P1/P2 giữ các module nguyên bản nhưng chỉ bật nhãn tiếng Việt sau khi dịch đầy đủ và kiểm tra nghiệp vụ.

## 3. Danh mục màn hình và thông số lưới
| ID | Màn hình | Cột dữ liệu chính | Actions |
|---|---|---|---|
| UI-VN-EMP-01 | Danh sách nhân viên | Mã NV, Họ và tên, Pháp nhân, Phòng ban, Chức danh, Loại HĐ, Trạng thái | Xem hồ sơ, Chỉnh sửa, Điều chuyển |
| UI-VN-EMP-02 | Hồ sơ nhân viên | Tab Cá nhân, Công việc, Hợp đồng, Thuế/BH, Ngân hàng, Lịch sử | Lưu nháp, Gửi duyệt, Xem lịch sử |
| UI-VN-CON-01 | Danh sách HĐ | Mã HĐ, NV, Loại, Ngày ký, Bắt đầu, Kết thúc, Trạng thái | Lập phụ lục, Gia hạn, Chấm dứt |
| UI-VN-ATT-01 | Chấm công hằng ngày | Ngày công, Ca, Vào, Ra, Giờ làm, Đi muộn, OT, Ngoại lệ | Giải trình, Yêu cầu sửa |
| UI-VN-ATT-02 | Bảng công tháng | NV, Công chuẩn, Công hưởng lương, Nghỉ có/không lương, OT, Chênh lệch | Đối soát, Chốt công |
| UI-VN-LEV-01 | Đơn nghỉ phép | NV, Loại, Từ, Đến, Số ngày, Người duyệt, Trạng thái | Gửi duyệt, Duyệt, Từ chối, Hủy đơn |
| UI-VN-LEV-02 | Sổ phép | NV, Dư đầu, Cấp, Đã dùng, Chuyển, Hết hạn, Dư cuối | Xem giao dịch, Điều chỉnh |
| UI-VN-PAY-01 | Kỳ lương | Kỳ, Pháp nhân, Công đã chốt, Số NV, Gross, Net, Tổng chi phí DN, Trạng thái | Tạo kỳ, Tính thử, Gửi duyệt |
| UI-VN-PAY-02 | Chi tiết bảng lương | NV, Lương HĐ, Công, OT, Phụ cấp, BH NLĐ, TNCN, Net, Cờ lỗi | Xem chi tiết, Duyệt, Khóa kỳ |
| UI-VN-PAY-03 | Phiếu lương | Thông tin kỳ, Thu nhập, Khấu trừ, Thuế, Bảo hiểm, Thực lĩnh | Tải PDF (đúng quyền) |
| UI-VN-RPT-01 | Báo cáo | Kỳ, Bộ lọc, Dataset, Tổng tiền, Phiên bản | Xem, Xuất Excel/PDF |
| UI-VN-ADM-01 | Phân quyền | Tài khoản, Vai trò, Pháp nhân, Đơn vị, Thời hạn | Cấp, Sửa, Thu hồi, Lịch sử |

## 4. Form và trình tự thao tác
**Tạo nhân viên**: bước 1 thông tin cơ bản (mã, tên, sinh nhật nếu có) → bước 2 công việc (pháp nhân, đơn vị, chức danh, điểm làm) → bước 3 định danh pháp lý (bảo vệ trường CCCD/BHXH/MST) → bước 4 hợp đồng và lịch làm → bước 5 rà soát. Cho phép Lưu nháp, rõ nội dung chưa đủ điều kiện kích hoạt; không buộc tạo CCCD giả.

**Duyệt nghỉ/OT**: chi tiết request hiển thị yêu cầu, người nộp, tác động đến công/phép/lương, nguồn lịch/quy tắc, lịch sử duyệt; nút Duyệt/Từ chối chỉ có nếu đúng quyền và kỳ chưa khóa.

**Tạo kỳ lương**: chọn pháp nhân, kỳ công, ngày dự kiến trả → preflight danh sách đủ/không đủ → tính thử → đối soát → Gửi duyệt → Duyệt → Phát hành phiếu → xác nhận thanh toán. Các tác vụ đã Paid chuyển sang luồng Điều chỉnh kỳ sau, không có nút “Sửa tiền” trực tiếp.

## 5. Từ vựng thao tác và trạng thái
| Ngữ cảnh | Nhãn chuẩn | Không dùng |
|---|---|---|
| Tạo bản nháp | Lưu nháp | Submit |
| Bắt đầu quy trình duyệt | Gửi duyệt | Gửi / Submit không rõ |
| Xác nhận hợp lệ | Phê duyệt | OK khi không rõ hậu quả |
| Không chấp thuận | Từ chối | Reject |
| Kết thúc nhập dữ liệu kỳ | Chốt bảng công / Chốt kỳ lương | Finish chung chung |
| Hủy tác vụ giao diện | Đóng | Hủy đơn nếu chỉ đóng modal |
| Thu hồi bản ghi khỏi truy cập thường | Lưu trữ | Xóa khi còn nghĩa vụ lưu |
| Trạng thái dữ liệu | Nháp / Chờ duyệt / Đã duyệt / Đã thanh toán / Đã hủy | Draft/Approved/Paid trên UI |
| Không được thao tác | Bạn không có quyền thực hiện thao tác này. | Unexpected error |
| Thiếu điều kiện trả lương | Không thể tính lương: bảng công kỳ này chưa được chốt. | Failed |
| Lỗi hợp đồng | Không xác định được hợp đồng có hiệu lực cho ngày đã chọn. | Contract error |
| Đơn phép trùng | Khoảng thời gian này đã có đơn nghỉ được ghi nhận. | Duplicate |
| Lỗi kết nối | Không thể hoàn tất yêu cầu. Vui lòng kiểm tra kết nối và thử lại. | Error 500 chung |

## 6. Quy tắc bảng dữ liệu
- Bộ lọc kỳ mặc định đúng pháp nhân đang chọn; trạng thái và hành động không gây mất bộ lọc khi quay lại.
- Sort ngày theo giá trị ngày, không theo chuỗi dd/MM/yyyy; tiền sort theo số, không theo ký hiệu VNĐ.
- Cho phép ẩn/hiện cột theo quyền, không bao giờ trả field nhạy cảm về client chỉ để ẩn CSS.
- Xuất file tuân theo filter/scope hiện tại; trước xuất tệp nhạy cảm hiển thị số lượng bản ghi, loại dữ liệu, lý do và xác nhận.
- Dialog xóa/hủy/chốt phải hiển thị tác động: số nhân viên, kỳ, khoản tiền/đơn bị ảnh hưởng.
- Hỗ trợ trạng thái không có dữ liệu, có lỗi tải, đang tải, không đủ quyền, đã chốt không thể sửa.

## 7. Kiểm thử UI bắt buộc
TC-UI-001: không có string EN trong luồng MVP ở menu, form, filter, confirm và email/PDF.  
TC-UI-002: màn hình công/lương giữ nguyên số liệu khi đổi ngôn ngữ, ngày và số tiền định dạng đúng.  
TC-UI-003: bảng dữ liệu 100/1.000 dòng có sort, filter, pagination giữ chính xác lựa chọn.  
TC-UI-004: nhân viên chỉ thấy phiếu của mình; UI không nhận dữ liệu lương của người khác trong network response.  
TC-UI-005: nút chốt kỳ có cảnh báo và không cho chốt khi tồn tại điều kiện BLOCKED.  
TC-UI-006: giao diện responsive desktop/tablet, không tràn nút, form/phân trang điều khiển được bằng bàn phím.

**Phê duyệt:** UX Lead + BA xác nhận nhãn/hành vi; HR và Kế toán xác nhận trạng thái/tiền; Tech Lead đảm bảo design system Horilla và API auth không bị thay đổi ngoài phạm vi.
