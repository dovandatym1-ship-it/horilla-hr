# VN-HRM | Quy ước tài liệu, thuật ngữ và phạm vi
**Mã tài liệu:** VNHRM-STD-00 · **Phiên bản:** 1.0 · **Ngày:** 17/10/2026 · **Trạng thái:** Dự thảo phân tích, chưa phê duyệt nghiệp vụ/pháp chế
**Baseline:** Horilla nhánh `2.0`, commit `fad3c73f212bd9a591b743024a1e6870e01f0f20` · **Chủ sở hữu duyệt:** BA Lead, Trưởng phòng Nhân sự, Kế toán tiền lương, Pháp chế, Tech Lead.

## 1. Mục tiêu và phạm vi
Phát triển phiên bản Horilla quản trị nhân sự phù hợp doanh nghiệp hoạt động tại Việt Nam, ưu tiên 20–500 lao động, có thể nhiều pháp nhân/điểm làm việc. Giữ chức năng cốt lõi, mở rộng quy tắc Việt Nam theo thời điểm hiệu lực, không giả định các quy tắc quốc tế hiện có tương thích luật Việt Nam. Tài liệu là **yêu cầu thiết kế**, không phải khẳng định chức năng đã được triển khai.

**Trong phạm vi MVP:** cơ cấu tổ chức, nhân viên, tài khoản/phân quyền, hợp đồng, ca và lịch làm việc, chấm công, nghỉ phép, chốt công, thành phần lương, bảo hiểm, thuế TNCN, phê duyệt kỳ lương, phiếu lương, báo cáo và nhật ký. **Ngoài MVP:** hồ sơ điện tử ký số tích hợp nhà cung cấp, cổng nộp BHXH/thuế tự động, thanh toán ngân hàng trực tiếp, mobile native, AI đánh giá nhân sự, full ERP.

## 2. Nguyên tắc chứng cứ
Mỗi phát biểu gắn loại:
- **AS-IS:** mã nguồn đã đọc, kèm file/model/đường dẫn GitHub. Không đồng nghĩa đã chạy phần mềm.
- **TO-BE:** chức năng hoặc kiến trúc cần xây.
- **LAW-CHECKED:** căn cứ có liên kết đến văn bản/nguồn nhà nước và ngày tra cứu; chưa thay ý kiến pháp chế.
- **POLICY:** nội quy/thoả ước/quy chế doanh nghiệp, chưa được mặc định là quy định pháp luật.
- **OPEN:** cần xác nhận và ghi người phê duyệt, ngày quyết định.
- **TEST:** kịch bản kiểm chứng có expected result; chưa mặc nhiên có kết quả Passed.

Không được ghi “đã hỗ trợ” chỉ dựa trên tên module. Số liệu luật và cấu hình tính lương phải có mã rule, phạm vi, hiệu lực từ/đến, phiên bản, căn cứ, trạng thái duyệt.

## 3. Cấu trúc định danh yêu cầu
| Đối tượng | Mã | Quy tắc |
|---|---|---|
| Epic | E-VN-01 … | Một phạm vi nghiệp vụ |
| Feature | F-VN-001 … | Có thể bàn giao độc lập |
| Use Case | UC-VN-EMP-001 | Diễn đạt hành vi có actor, trigger, pre/postconditions |
| Business Rule | BR-VN-PAY-001 | Một quy tắc kiểm tra/tính toán có thể test |
| Data Element | DE-VN-EMP-001 | Một trường dữ liệu |
| Acceptance Criteria | AC-VN-001 | Điều kiện có thể đo |
| Test Case | TC-VN-PAY-001 | Input, các bước, kết quả mong đợi |
| Decision | DEC-VN-001 | Vấn đề, lựa chọn, người duyệt |
| Legal Rule Set | LR-VN-PIT-2026-v1 | Bản luật hiệu lực có phiên bản |

Dùng mã cố định; không tái sử dụng mã đã hủy. Với field kỹ thuật dùng `snake_case`; nhãn UI dùng tiếng Việt; tên sự kiện/enum nội bộ dùng tiếng Anh ổn định. Một feature liên kết ít nhất 1 UC hoặc BR, 1 AC và 1 TC. Khi law changed: tạo phiên bản mới, không sửa hồi tố dữ liệu lương đã chốt.

## 4. Từ điển thuật ngữ nhất quán
| Thuật ngữ UI chính thức | Thuật ngữ thay thế không dùng | Diễn giải/thuộc tính |
|---|---|---|
| Nhân viên | Employee/người dùng (khi nói hồ sơ) | Cá nhân có hồ sơ lao động; có thể chưa có tài khoản |
| Tài khoản | Nhân viên | Danh tính đăng nhập, có thể gắn 1 hồ sơ nhân viên |
| Pháp nhân/Công ty | Chi nhánh | Đơn vị chịu nghĩa vụ lao động/thuế riêng |
| Đơn vị/Phòng ban | Department | Cấu trúc quản trị nội bộ |
| Địa điểm làm việc | Địa chỉ thường trú | Nơi bố trí làm việc, dùng để xác định vùng áp dụng khi phù hợp |
| Hợp đồng lao động (HĐLĐ) | Contract chung | Hợp đồng theo phân loại pháp lý, phụ lục và lịch sử |
| Chấm công | Check-in đơn thuần | Xác nhận thời gian/công thực tế và kết quả xử lý |
| Bảng công | Bảng lương | Số liệu công/nghỉ/OT đã đối soát theo kỳ |
| Công chuẩn | Số ngày hiện diện | Số ngày/giờ chuẩn theo lịch áp dụng từng nhân viên/kỳ |
| Ngày công hưởng lương | Công có mặt | Bao gồm loại vắng mặt hưởng lương theo chính sách |
| Làm thêm giờ (OT) | Giờ làm việc bình thường | Giờ vượt lịch được duyệt theo quy tắc |
| Nghỉ phép năm | Nghỉ nói chung | Loại nghỉ có số dư và cơ chế tích lũy/quy đổi |
| Tổng thu nhập | Lương thực nhận | Thu nhập trong kỳ trước khấu trừ |
| Lương Gross | Lương Net | Gross trước các khoản khấu trừ người lao động; Net thực lĩnh |
| Thu nhập tính thuế | Tổng thu nhập | Sau phân loại và các khoản được trừ phù hợp |
| BHXH/BHYT/BHTN | Bảo hiểm nói chung | Ba nghĩa vụ tách riêng, không gộp tỷ lệ |
| Thuế TNCN | Thuế thu nhập doanh nghiệp | Nghĩa vụ khấu trừ của cá nhân |
| Kỳ lương | Ngày trả lương | Khoảng được tính; ngày chi trả là thuộc tính riêng |
| Chốt kỳ lương | Phê duyệt bảng lương | Đóng băng nguồn, ký duyệt, khóa điều chỉnh tùy trạng thái |
| Phiếu lương | File Excel tính thử | Kết quả cá nhân, phân quyền riêng |
| Truy lĩnh/truy thu | Sửa phiếu đã trả | Điều chỉnh có lý do kỳ sau, duy trì lịch sử |
| Người phụ thuộc | Số con | Đối tượng đủ điều kiện khấu trừ thuế theo kỳ, hồ sơ riêng |
| Phạm vi dữ liệu | Vai trò chức năng | Giới hạn xem/sửa theo pháp nhân, phòng ban, nhân viên |

## 5. Quy ước UI và dữ liệu
- Toàn bộ menu, màn hình, form, thông báo, trạng thái, bảng và nhãn xuất phải tiếng Việt có dấu; giữ thuật ngữ kỹ thuật ở tài liệu phụ lục. Tên người và địa chỉ lưu Unicode NFC, tìm kiếm không dấu không làm mất dữ liệu gốc.
- Hiển thị ngày `dd/MM/yyyy`, thời gian 24 giờ, múi giờ `Asia/Ho_Chi_Minh`; lưu thời điểm UTC và kèm timezone khi trao đổi API. Không nhập nhằng `date` và `datetime`.
- VND hiển thị `1.234.567 ₫`; lưu số nguyên đồng hoặc Decimal được chốt chính sách làm tròn. API ghi đơn vị rõ, không lưu ký hiệu tiền vào giá trị số.
- Địa chỉ: Tỉnh/Thành phố → Xã/Phường/Đặc khu theo dữ liệu hiện hành; quận/huyện nếu còn trong lịch sử chỉ dùng như trường lịch sử/địa chỉ cũ, **không** áp đặt cấp quản lý huyện vào quy trình mới.
- Form có nhãn bắt buộc, định dạng, cảnh báo, người cập nhật và lịch sử; phân biệt “Lưu nháp”, “Gửi duyệt”, “Phê duyệt”, “Từ chối”, “Chốt”, “Hủy”.
- Tìm kiếm, sắp xếp, lọc và xuất dữ liệu phải tôn trọng chính xác quyền dữ liệu; số lượng kết quả cũng không tiết lộ dữ liệu pháp nhân khác.

## 6. Ma trận vai trò nghiệp vụ
| Vai trò | Phạm vi tối thiểu |
|---|---|
| Quản trị nền tảng | Cấu hình kỹ thuật, không mặc nhiên xem lương chi tiết |
| HR Admin | Hồ sơ nhân viên, hợp đồng, cơ cấu được phân công |
| HR Operations | Điều chỉnh công, nghỉ, ca và yêu cầu theo đơn vị |
| Payroll Specialist | Chuẩn bị bảng công/lương, nhập thành phần được phép |
| Payroll Approver | Duyệt kỳ lương, không tự duyệt thay đổi do chính mình tạo nếu có phân tách nhiệm vụ |
| Kế toán/Tài chính | Xem kết quả chi trả/bút toán, mức truy cập theo nhiệm vụ |
| Quản lý trực tiếp | Xem nhân sự thuộc phạm vi và duyệt nghỉ/OT, không xem lương nếu không được cấp |
| Nhân viên (ESS) | Xem hồ sơ, công, phép, phiếu lương của chính mình |
| Kiểm toán | Chỉ đọc log và bằng chứng trong phạm vi được cấp, có lịch sử truy cập |

## 7. Định nghĩa hoàn thành tài liệu
Mỗi tài liệu có mã, phiên bản, ngày, người phê duyệt, phạm vi, chứng cứ AS-IS, TO-BE, ngoại lệ, BR, dữ liệu, phân quyền, TC, trace sang source code và backlog. Các mục chưa đủ luật hoặc quyết định quy chế phải ghi **OPEN/BLOCKED**; không được hợp thức hóa bằng số liệu mẫu.

## 8. Phụ lục v1.1 — Chuẩn trạng thái yêu cầu và mã lỗi
**CODE_STATIC_ONLY** = thấy field/model/guard trong code nhưng chưa chạy runtime; **AS_IS_VERIFIED** = hành vi được xác nhận bằng bằng chứng có version; **TO_BE** = cần triển khai; **BLOCKED_BY_POLICY** = thiếu quyết định nghiệp vụ được phê duyệt; **NOT_RUN** = chưa chạy testcase; **PASS** = có run evidence. Không dùng từ “đã hỗ trợ” cho hành vi thuộc TO_BE.

Mỗi yêu cầu chi tiết phải liên kết \`F/UC/BR/DE/WF/UI/API/TC\` và có vai trò phê duyệt; không đặt \`Implemented\` chỉ vì có bản nháp trong docs. Validation chuẩn tại [10](10-FIELD-LEVEL-VALIDATION-MATRIX.md); UI action tại [11](11-UI-FORM-ACTION-SPECIFICATION.md); lỗi API tại [14](14-API-PERMISSION-ERROR-CONTRACT.md).
