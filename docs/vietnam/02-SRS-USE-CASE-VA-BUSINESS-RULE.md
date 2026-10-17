# VN-HRM | SRS: Use Case và Business Rules
**Mã:** VNHRM-SRS-02 · **Phiên bản:** 1.0 · **Trạng thái:** Dự thảo · **Đối chiếu:** BRD-01, STD-00

## 1. Nguyên tắc kỹ thuật của yêu cầu
Mọi UC bắt buộc xác nhận: trigger; actor/chức năng; preconditions; dữ liệu vào; luồng chính; nhánh/ngoại lệ; hậu điều kiện; phân quyền; audit; TC. Không phát sinh hành động ngoại hệ thống (chuyển khoản/nộp BHXH/khai thuế) chỉ nhờ người dùng nhấn nút “Xuất” hay “Chốt”. Đối với API: validator ở server, transaction đối với số dư/tiền, idempotency-key với thao tác lặp, mã lỗi ổn định.

## 2. Danh sách Use Case chuẩn hóa
| UC | Actor | Trigger và tiền điều kiện | Xử lý chính và kết quả |
|---|---|---|---|
| UC-VN-ORG-001 | HR Admin | Tạo pháp nhân/chi nhánh | Kiểm tra mã, MST, thời điểm hiệu lực; thiết lập địa chỉ và phạm vi dữ liệu |
| UC-VN-ORG-002 | HR Admin | Điều chuyển nhân viên | Tạo sự kiện chuyển vị trí/công ty theo ngày, không ghi đè lịch sử |
| UC-VN-EMP-001 | HR | Tiếp nhận NV từ onboarding | Chống trùng; mã nội bộ; dữ liệu pháp lý; trạng thái Draft/Active |
| UC-VN-EMP-002 | NLĐ/HR | Sửa hồ sơ nhạy cảm | Yêu cầu duyệt/đối chiếu; mã hóa/che dữ liệu; log truy cập |
| UC-VN-EMP-003 | Payroll | Đăng ký người phụ thuộc | Điều kiện hồ sơ, khoảng hiệu lực, cảnh báo trùng |
| UC-VN-CON-001 | HR | Lập/kích hoạt HĐ | Loại HĐ, điều khoản, hiệu lực, phê duyệt và snapshot |
| UC-VN-CON-002 | HR | Sửa đổi lương/HĐ | Lập phụ lục, truy vết bản cũ, quyết định tác động hồi tố |
| UC-VN-ATT-001 | HR | Công bố lịch/ca | Áp dụng theo địa điểm và ngày; khóa lịch quá khứ có giải trình |
| UC-VN-ATT-002 | Nhân viên | Check-in/out | Ghi log gốc, chống trùng, bảo toàn timezone và nguồn |
| UC-VN-ATT-003 | NV/Manager/HR | Thiếu công hoặc xin sửa | Yêu cầu + bằng chứng → duyệt → kết quả công, không xóa log |
| UC-VN-ATT-004 | Manager | Đăng ký OT | Phân loại ngày/giờ; duyệt và giới hạn theo pháp luật/chính sách |
| UC-VN-ATT-005 | HR | Chốt công | So khớp nghỉ và OT, giải quyết xung đột, khóa theo kỳ/version |
| UC-VN-LEV-001 | Nhân viên | Gửi đơn nghỉ | Kiểm tra loại, lịch, số dư, người duyệt; giữ quyền lợi |
| UC-VN-LEV-002 | Manager/HR | Duyệt/hủy nghỉ | Ghi ledger và tác động chấm công, idempotent |
| UC-VN-LEV-003 | HR | Tính phép năm/thâm niên | Rule effective-date, prorate, điều chỉnh số dư và bảo toàn ledger |
| UC-VN-PAY-001 | Payroll | Tạo kỳ lương | Chọn pháp nhân/kỳ/nhân viên, chụp cấu hình và công đã khóa |
| UC-VN-PAY-002 | Payroll | Tính thử | Thu nhập, bảo hiểm, thuế, khấu trừ, kết quả per-employee giải thích được |
| UC-VN-PAY-003 | Approver | Phê duyệt lương | Duyệt theo quyền; tách người tạo và duyệt; immutable snapshot |
| UC-VN-PAY-004 | Finance | Đánh dấu đã chi | Đối soát file/bank acknowledgment, lưu ref, Paid terminal |
| UC-VN-PAY-005 | Payroll | Tính điều chỉnh kỳ sau | Tạo delta có tham chiếu kỳ/phiếu gốc và lý do |
| UC-VN-RPT-001 | HR/Finance | Lập báo cáo | Lọc đúng pháp nhân/đơn vị; PDF/XLSX có truy vết |
| UC-VN-SEC-001 | Admin | Cấp quyền | Áp dụng RBAC + data scope + mask fields và audit |
| UC-VN-OFF-001 | HR | Chấm dứt HĐ | Báo trước (theo trường hợp), chốt công/đối soát, thu hồi tài khoản |

## 3. UC chi tiết – Tạo và phê duyệt kỳ lương (UC-VN-PAY-001→004)
**Actor:** Payroll Specialist, Approver, Finance. **Tiền điều kiện:** công đã chốt; nhân viên có HĐ phù hợp; rule set pháp lý `approved`; người dùng thuộc pháp nhân hợp lệ; dữ liệu bảo hiểm/người phụ thuộc đủ điều kiện hoặc đã được gắn ngoại lệ có phê duyệt.

**Luồng chính:** 1) Chọn pháp nhân, kỳ tính, ngày dự kiến trả. 2) Kiểm tra trùng kỳ; giải thích các nhân viên không đủ điều kiện. 3) Lấy version hợp đồng, lịch, bảng công, nghỉ, OT, đối tượng tính BH/thuế. 4) Tạo snapshot đầu vào và `payroll_run_id`. 5) Xây earning lines có mã và nhóm chịu thuế/BH; tính statutory deduction/tax; tính net; chụp rule version và rounding policy. 6) Hiển thị reconcile: gross/net, employer cost, ngoại lệ và chênh lệch với kỳ trước. 7) Người tạo submit; Approver kiểm tra và approve. 8) Chốt file chi trả; Finance xác minh trạng thái thanh toán, đánh dấu Paid với mã tham chiếu. 9) Phát hành phiếu lương cho ESS.

**Ngoại lệ:** có log chấm công chưa duyệt ⇒ blocked; rule chưa duyệt ⇒ blocked; nhân viên 2 HĐ hoạt động xung đột ⇒ blocked; người phụ thuộc thiếu ngày hiệu lực ⇒ flagged/review; net âm ⇒ blocked trừ khi cơ chế được duyệt; duplicate submit ⇒ trả run trước không tạo đôi; ngân hàng từ chối một nhân viên ⇒ giữ trạng thái chưa hoàn tất theo thiết kế đối soát, không tự đánh dấu tất cả Paid.

**Hậu điều kiện:** tiền theo người, pháp nhân và kỳ cân bằng; record audit; một snapshot có hash; đã Paid không bị update giá trị.

## 4. UC chi tiết – Duyệt nghỉ (UC-VN-LEV-001/002)
**Pre:** NLĐ đang có hiệu lực, được gán lịch, loại nghỉ hợp lệ, quyền người duyệt. 1) Chọn loại/khoảng thời gian/nửa ngày; 2) hệ thống lấy lịch và ngày nghỉ lễ hiệu lực; 3) tính requested days và dự báo số dư; 4) kiểm tra xung đột đơn khác/công hoặc kỳ đã chốt; 5) Submit; 6) duyệt có log; 7) ledger ghi debit đúng một lần; 8) cập nhật chấm công nguồn. Trùng lần bấm Approve không được trừ thêm; Cancel có hoàn phép đúng một lần nếu policy cho phép; không trả phép khi đã Paid nếu chưa mở quy trình adjustment.

## 5. UC chi tiết – Sửa công (UC-VN-ATT-003)
Yêu cầu sửa chứa ngày công, log gốc, giá trị đề xuất, lý do, tài liệu, người xác nhận. Người được duyệt không mặc nhiên là người gửi. Quản lý duyệt; hệ thống tạo bản điều chỉnh tách log gốc và dấu vết. Nếu kỳ công khóa, mở yêu cầu chỉnh kỳ và có nhánh payroll adjustment; không sửa dữ liệu đã trả lương trực tiếp.

## 6. Business Rules bắt buộc
| Mã | Quy tắc và quyết định hệ thống | Ví dụ TC |
|---|---|---|
| BR-VN-ORG-001 | Dữ liệu nhân viên theo đúng pháp nhân và lịch sử điều chuyển; không lấy pháp nhân từ header do client tự gửi nếu chưa xác thực quyền | TC-SEC-001 |
| BR-VN-ORG-002 | Tỉnh/xã có mã, tên và khoảng hiệu lực; địa chỉ cũ được giữ bản chụp | TC-ORG-002 |
| BR-VN-EMP-001 | Employee ID bất biến; CCCD/MST/BHXH là định danh nhạy cảm có lịch sử và quyền phù hợp | TC-EMP-001 |
| BR-VN-EMP-002 | Trùng định danh cần quy trình xử lý; không âm thầm gộp hồ sơ | TC-EMP-003 |
| BR-VN-EMP-003 | Người phụ thuộc có loại quan hệ, mã/hồ sơ, `valid_from` và `valid_to`, trạng thái xác nhận; không dùng `Employee.children` để tính thuế | TC-PIT-003 |
| BR-VN-CON-001 | Chọn HĐ đang hiệu lực theo ngày công/kỳ lương; giao nhau bất hợp lệ tạo lỗi giải quyết xung đột | TC-CON-002 |
| BR-VN-CON-002 | Phụ lục lương có hiệu lực về sau không làm thay số liệu kỳ cũ đã Paid | TC-CON-004 |
| BR-VN-ATT-001 | Log gốc bất biến; sửa công lưu delta và actor | TC-ATT-002 |
| BR-VN-ATT-002 | Ca 22:00–06:00 qua ngày tính theo vùng thời gian/ca gán, không tự tạo hai ngày công | TC-ATT-004 |
| BR-VN-ATT-003 | OT chỉ tính theo giờ được duyệt và pháp luật/chính sách áp dụng; không cộng trùng loại ngày | TC-OT-001 |
| BR-VN-ATT-004 | Phân loại ngày thường, nghỉ hằng tuần, lễ và ca đêm; trùng phân loại có thứ tự ưu tiên được duyệt | TC-OT-002 |
| BR-VN-ATT-005 | Không chốt công khi còn thiếu/đụng log chưa xử lý quá ngưỡng quy chế | TC-ATT-005 |
| BR-VN-LEV-001 | Số ngày phép được tính theo lịch mỗi người, không mặc định ngày nào cũng 1 công | TC-LEV-001 |
| BR-VN-LEV-002 | Mỗi request được ghi ledger một lần, approve/cancel idempotent | TC-LEV-002 |
| BR-VN-LEV-003 | Nguồn phép đầu kỳ, accrual, carryforward, debit, credit, expiry phải đối soát thành công | TC-LEV-003 |
| BR-VN-PAY-001 | Công chưa khóa hoặc lương chưa được gán version rules ⇒ không phát hành phiếu chính thức | TC-PAY-001 |
| BR-VN-PAY-002 | Tính tiền theo đơn vị VND với chính sách làm tròn thống nhất và test edge-cases | TC-PAY-002 |
| BR-VN-PAY-003 | Người lao động và doanh nghiệp có khoản đóng bảo hiểm phân biệt; không cộng employer cost vào net của NLĐ | TC-INS-001 |
| BR-VN-PAY-004 | Thu nhập chịu thuế là phân loại từng earning, không mặc định tất cả allowance đều chịu thuế | TC-PIT-001 |
| BR-VN-PAY-005 | Giảm trừ người phụ thuộc theo kỳ/đủ điều kiện/đã xác nhận, không dựa trên số trẻ | TC-PIT-003 |
| BR-VN-PAY-006 | Policy lookup theo pháp nhân, loại NLĐ, kỳ hiệu lực, ưu tiên; thiếu/mâu thuẫn ⇒ fail closed | TC-PAY-004 |
| BR-VN-PAY-007 | Mọi khoản trả trong kỳ có dòng trace `source_id`, `rule_id`, `rule_version`, `rounding`, `amount` | TC-PAY-006 |
| BR-VN-PAY-008 | Đã Paid không sửa; correction kỳ sau là delta có lý do và approval | TC-PAY-005 |
| BR-VN-RPT-001 | Báo cáo/API/export không truy cập vượt scope; field lương/CCCD mask theo quyền | TC-SEC-002 |
| BR-VN-SEC-001 | Ủy quyền duyệt phải giới hạn thời gian và pháp nhân; self-approval phải kiểm soát | TC-SEC-003 |
| BR-VN-SEC-002 | Nhật ký mọi xem/xuất thông tin nhạy cảm và phê duyệt được lưu không ghi đè | TC-SEC-004 |

## 7. Yêu cầu phi chức năng (NFR)
**Bảo mật:** OWASP ASVS làm chuẩn tham khảo; HTTPS, cookie/JWT đúng settings, session expiration, rate limit, dữ liệu nhạy cảm mã hóa ở mức phù hợp; kiểm soát mặt cắt dữ liệu import/export. **Tính đúng:** tính lại snapshot cùng input+rule version phải ra cùng kết quả; không phụ thuộc giờ chạy. **Tin cậy:** backup+khôi phục được thử nghiệm; failure từng nhân viên không làm trôi số tiền các nhân viên khác. **Hiệu năng:** benchmark ít nhất 100/500/1.000 nhân viên với công+phép+lương và trích xuất; ngưỡng thời gian cần đo baseline trước khi cam kết. **Khả dụng:** form có trạng thái lỗi, hỗ trợ bàn phím, xử lý tiếng Việt không lỗi Unicode.

## 8. Truy vết và tiêu chí phê duyệt
Thiết lập trace theo chuỗi `F → UC → BR → DE → API/Model → AC → TC → PR`. Không phát triển tác vụ có nhiều giả định luật chưa duyệt; tách rõ mục `BLOCKED_BY_POLICY`. Trưởng HR/Kế toán/Pháp chế đồng duyệt các BR tiền lương; Tech Lead và QA duyệt triển khai/test.
