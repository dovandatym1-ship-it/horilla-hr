# VN-HRM | Đặc tả chi tiết toàn bộ Use Case
**ID:** VNHRM-UC-12 · **Phiên bản:** 1.1 · **Ngày:** 18/10/2026 · **Trạng thái:** DRAFT, gồm TO-BE và khoảng trống so với PR #3; chưa nghiệm thu pháp lý/QA.

## 1. Mẫu UC bắt buộc
Mỗi UC có actor, trigger, quyền/scope, tiền điều kiện (PRE), luồng chính (MAIN) theo thứ tự giao diện/API, nhánh thay thế/ngoại lệ (ALT), hậu điều kiện (POST), bản ghi/audit (AUDIT), validation (DE/BR) và test liên quan (TC). Ngoại lệ business trả mã ổn định theo tài liệu 14, không trả lỗi 500 chung. Mọi thao tác có tiền/số dư/chốt kỳ cần transaction, khóa cạnh tranh và idempotency. Không thể dùng quy trình TO-BE để khẳng định Horilla AS-IS đã thực hiện.

**Quy ước nhãn:** [CODE] đã thấy ở code mới; [SPEC] cần phát triển; [POLICY] phụ thuộc phê duyệt HR/Kế toán/Pháp chế. Dữ liệu nhạy cảm lưu tham chiếu mã hóa và che theo quyền; không log raw.

## 2. Danh mục và chi tiết 23 Use Case
### 1. UC-VN-ORG-001 — Tạo pháp nhân và địa điểm
- **Actor/trigger:** HR Admin; khởi phát bởi tác vụ người dùng, sự kiện tích hợp hoặc lịch hiệu lực; xác thực và scope server-side.
- **PRE:** Pháp nhân được phê duyệt, có mã/loại và quyền quản trị tổ chức.
- **MAIN:** (1) Tạo pháp nhân → (2) nhập mã/tên/MST/địa chỉ → (3) chọn tỉnh-xã và hiệu lực → (4) xác định nơi làm việc/vùng lương có version → (5) đối chiếu duplicate → (6) lưu Draft và kích hoạt sau phê duyệt.
- **ALT/EXCEPTION:** Trùng mã/MST phải đối soát, không tự merge; địa giới hết hiệu lực hoặc địa điểm không xác định thì không publish. Mọi lỗi trước commit không tạo kết quả một phần; báo field và mã lỗi quy định.
- **POST/AUDIT:** Có legal entity và work location theo version; không làm thay đổi payroll quá khứ. Ghi actor, timestamp, pháp nhân, event/source, before/after khi có thay đổi, correlation ID.
- **Trace:** DE-VN-ORG-001..006; BR-VN-ORG-001/002; TC-ORG-001/002. Trạng thái triển khai xác nhận qua [bảng GAP](16-CODE-TO-DOC-GAP.md).

### 2. UC-VN-ORG-002 — Điều chuyển nhân viên
- **Actor/trigger:** HR, HR Manager; khởi phát bởi tác vụ người dùng, sự kiện tích hợp hoặc lịch hiệu lực; xác thực và scope server-side.
- **PRE:** Nhân viên hiện có; nơi đi/đến tồn tại và người dùng có quyền hai bên.
- **MAIN:** (1) Chọn nhân viên → (2) chọn pháp nhân/đơn vị/chức danh mới → (3) nhập ngày hiệu lực và lý do → (4) so sánh lịch/HĐ/phép/thuế-BH → (5) trình duyệt → (6) tạo assignment mới, kết thúc assignment cũ theo policy.
- **ALT/EXCEPTION:** Chặn xung đột kỳ công đã chốt, đổi pháp nhân khi thiếu HĐ hoặc quyền; điều chuyển hồi tố đi vào luồng adjustment. Mọi lỗi trước commit không tạo kết quả một phần; báo field và mã lỗi quy định.
- **POST/AUDIT:** Lưu history old/new, báo tác động cho Payroll và bảo toàn dữ liệu ở nơi cũ. Ghi actor, timestamp, pháp nhân, event/source, before/after khi có thay đổi, correlation ID.
- **Trace:** DE-VN-EMP-009..011; BR-VN-ORG-001; TC-ORG-003;TC-SEC-001. Trạng thái triển khai xác nhận qua [bảng GAP](16-CODE-TO-DOC-GAP.md).

### 3. UC-VN-EMP-001 — Tiếp nhận nhân viên
- **Actor/trigger:** HR, Onboarding; khởi phát bởi tác vụ người dùng, sự kiện tích hợp hoặc lịch hiệu lực; xác thực và scope server-side.
- **PRE:** Ứng viên đủ điều kiện tiếp nhận; có quyền đơn vị; chưa có nhân viên trùng được xác nhận.
- **MAIN:** (1) Chọn nguồn onboarding → (2) nhập mã và tên → (3) chọn công ty/bộ phận/chức danh → (4) nhập thông tin pháp lý theo mức sẵn có → (5) kiểm tra trùng định danh qua vault (nếu có) → (6) tạo Draft → (7) kiểm tra điều kiện Active và kích hoạt.
- **ALT/EXCEPTION:** Thiếu CCCD hợp lệ nhưng được phép Draft thì gắn cần bổ sung; nghi trùng không gộp, chuyển xác minh; thiếu HĐ/lịch theo policy thì chặn Active. Mọi lỗi trước commit không tạo kết quả một phần; báo field và mã lỗi quy định.
- **POST/AUDIT:** Có Employee và hồ sơ tham chiếu có phạm vi, nhật ký nguồn và trạng thái. Ghi actor, timestamp, pháp nhân, event/source, before/after khi có thay đổi, correlation ID.
- **Trace:** DE-VN-EMP-001..011; BR-VN-EMP-001/002; TC-EMP-001/003. Trạng thái triển khai xác nhận qua [bảng GAP](16-CODE-TO-DOC-GAP.md).

### 4. UC-VN-EMP-002 — Thay đổi hồ sơ nhạy cảm
- **Actor/trigger:** NLĐ, HR, verifier; khởi phát bởi tác vụ người dùng, sự kiện tích hợp hoặc lịch hiệu lực; xác thực và scope server-side.
- **PRE:** Đã đăng nhập, có quyền xem/sửa theo bản thân hoặc HR phân công; có mục đích hợp lệ.
- **MAIN:** (1) Chọn trường cần thay → (2) nhập/chọn tài liệu xác thực qua kênh bảo vệ → (3) kiểm tra định dạng/duplicate → (4) gửi xác minh → (5) verifier độc lập chấp thuận/từ chối → (6) cập nhật tham chiếu, giữ lịch sử và audit.
- **ALT/EXCEPTION:** Không có quyền => từ chối không lộ raw; trùng định danh => manual review; vault lỗi => không update một phần. Mọi lỗi trước commit không tạo kết quả một phần; báo field và mã lỗi quy định.
- **POST/AUDIT:** Lưu version và evidence, chỉ expose mask cho vai trò không có quyền raw. Ghi actor, timestamp, pháp nhân, event/source, before/after khi có thay đổi, correlation ID.
- **Trace:** DE-VN-EMP-002..008; BR-VN-EMP-001/002; TC-EMP-002;TC-SEC-004. Trạng thái triển khai xác nhận qua [bảng GAP](16-CODE-TO-DOC-GAP.md).

### 5. UC-VN-EMP-003 — Đăng ký người phụ thuộc
- **Actor/trigger:** NLĐ, HR, Payroll; khởi phát bởi tác vụ người dùng, sự kiện tích hợp hoặc lịch hiệu lực; xác thực và scope server-side.
- **PRE:** Hồ sơ nhân viên có pháp nhân và thời điểm yêu cầu, có danh mục quan hệ được phê duyệt.
- **MAIN:** (1) Nhập họ tên/quan hệ/ngày sinh/hiệu lực → (2) đính bằng chứng và định danh qua vault → (3) kiểm tra khoảng hiệu lực và nguy cơ trùng → (4) gửi xác minh → (5) Payroll/HR kiểm tra điều kiện → (6) ghi trạng thái/evidence.
- **ALT/EXCEPTION:** Không đủ hồ sơ => pending; trùng quyền lợi/cùng cá nhân theo policy => yêu cầu đối soát; rejected cần lý do; thay đổi hồi tố không sửa trực tiếp PIT Paid. Mọi lỗi trước commit không tạo kết quả một phần; báo field và mã lỗi quy định.
- **POST/AUDIT:** Lịch sử eligibility/verification phục vụ kỳ thuế nhưng chưa tự khấu trừ nếu chưa có integration. Ghi actor, timestamp, pháp nhân, event/source, before/after khi có thay đổi, correlation ID.
- **Trace:** DE-VN-DEP-001..005; BR-VN-EMP-003; BR-VN-PAY-005; TC-PIT-002/003. Trạng thái triển khai xác nhận qua [bảng GAP](16-CODE-TO-DOC-GAP.md).

### 6. UC-VN-CON-001 — Lập và kích hoạt hợp đồng
- **Actor/trigger:** HR, approver; khởi phát bởi tác vụ người dùng, sự kiện tích hợp hoặc lịch hiệu lực; xác thực và scope server-side.
- **PRE:** Nhân viên và pháp nhân hợp lệ; người ký được ủy quyền; loại HĐ và chính sách có hiệu lực.
- **MAIN:** (1) Chọn nhân viên → (2) chọn loại HĐ/vị trí/địa điểm → (3) nhập số HĐ, ngày ký, kỳ hạn, điều khoản lương → (4) kiểm tra tối thiểu vùng/overlap → (5) tạo Draft → (6) submit và approve → (7) kích hoạt theo ngày hiệu lực.
- **ALT/EXCEPTION:** Xung đột hợp đồng, lương không đáp ứng quy tắc hoặc hợp đồng thiếu chữ ký => chặn Active; thiếu policy => BLOCKED_BY_POLICY. Mọi lỗi trước commit không tạo kết quả một phần; báo field và mã lỗi quy định.
- **POST/AUDIT:** Hợp đồng versioned có evidence; gửi thay đổi đến lịch công, BH và payroll tương lai. Ghi actor, timestamp, pháp nhân, event/source, before/after khi có thay đổi, correlation ID.
- **Trace:** DE-VN-CON-001..005; BR-VN-CON-001; TC-CON-002;TC-CON-003. Trạng thái triển khai xác nhận qua [bảng GAP](16-CODE-TO-DOC-GAP.md).

### 7. UC-VN-CON-002 — Lập phụ lục điều chỉnh lương
- **Actor/trigger:** HR, contract approver; khởi phát bởi tác vụ người dùng, sự kiện tích hợp hoặc lịch hiệu lực; xác thực và scope server-side.
- **PRE:** Contract thuộc pháp nhân; người lập khác người duyệt; ngày hiệu lực xác định.
- **MAIN:** (1) Chọn HĐ gốc → (2) nhập amendment_code, effective_date, new_monthly_wage_vnd và lý do → (3) kiểm tra unique/range/minimum/overlap → (4) lưu Draft → (5) approver duyệt → (6) ghi quyết định bất biến → (7) tạo lịch sử áp dụng và phát sự kiện payroll.
- **ALT/EXCEPTION:** Không tự duyệt, không sửa approved; hồi tố vào kỳ Paid => tạo payroll adjustment, không ghi đè; HĐ gốc không phù hợp => block. Mọi lỗi trước commit không tạo kết quả một phần; báo field và mã lỗi quy định.
- **POST/AUDIT:** Có amendment approved và event áp dụng; bước cập nhật Contract.wage [SPEC, chưa có ở PR #3]. Ghi actor, timestamp, pháp nhân, event/source, before/after khi có thay đổi, correlation ID.
- **Trace:** DE-VN-CON-004/005; BR-VN-CON-002; TC-CON-001/004. Trạng thái triển khai xác nhận qua [bảng GAP](16-CODE-TO-DOC-GAP.md).

### 8. UC-VN-ATT-001 — Công bố lịch và phân ca
- **Actor/trigger:** HR, manager; khởi phát bởi tác vụ người dùng, sự kiện tích hợp hoặc lịch hiệu lực; xác thực và scope server-side.
- **PRE:** Chính sách ca và địa điểm được phê duyệt; quyền trong phạm vi nhân viên.
- **MAIN:** (1) Chọn chu kỳ/lịch → (2) khai báo ca start/end, nghỉ giữa ca, work_date_rule → (3) gán người/địa điểm → (4) kiểm tra trùng lịch, ngày lễ, ca qua đêm → (5) trình duyệt → (6) publish version theo hiệu lực.
- **ALT/EXCEPTION:** Lịch quá khứ hoặc kỳ locked => nhánh reopen/adjustment; conflict assignment => chặn hoặc quy tắc ưu tiên đã duyệt. Mọi lỗi trước commit không tạo kết quả một phần; báo field và mã lỗi quy định.
- **POST/AUDIT:** Roster snapshot và audit thông báo cho nhân viên. Ghi actor, timestamp, pháp nhân, event/source, before/after khi có thay đổi, correlation ID.
- **Trace:** DE-VN-ATT-002/004; BR-VN-ATT-002; TC-ATT-004. Trạng thái triển khai xác nhận qua [bảng GAP](16-CODE-TO-DOC-GAP.md).

### 9. UC-VN-ATT-002 — Ghi nhận check-in/check-out
- **Actor/trigger:** NLĐ, máy chấm công, import; khởi phát bởi tác vụ người dùng, sự kiện tích hợp hoặc lịch hiệu lực; xác thực và scope server-side.
- **PRE:** Thiết bị hoặc nhân viên được xác thực; employee mapping, source và timezone đầy đủ.
- **MAIN:** (1) Nhận source/event_id/timestamp → (2) validate signature/identity → (3) idempotency theo source+external_event_id → (4) lưu raw immutable → (5) ghép vào ca phù hợp → (6) gắn ngoại lệ nếu thiếu/mâu thuẫn.
- **ALT/EXCEPTION:** Duplicate trả sự kiện trước; unknown employee/device ghi quarantine không tạo công giả; ca qua đêm giữ work_date theo roster. Mọi lỗi trước commit không tạo kết quả một phần; báo field và mã lỗi quy định.
- **POST/AUDIT:** Raw log không ghi đè; work result có nguồn và trạng thái. Ghi actor, timestamp, pháp nhân, event/source, before/after khi có thay đổi, correlation ID.
- **Trace:** DE-VN-ATT-001..004; BR-VN-ATT-001/002; TC-ATT-001/003/004. Trạng thái triển khai xác nhận qua [bảng GAP](16-CODE-TO-DOC-GAP.md).

### 10. UC-VN-ATT-003 — Yêu cầu và duyệt sửa công
- **Actor/trigger:** Employee, Manager, HR; khởi phát bởi tác vụ người dùng, sự kiện tích hợp hoặc lịch hiệu lực; xác thực và scope server-side.
- **PRE:** Có ca và ngày công, không mất log gốc, quyền reviewer không trùng người gửi.
- **MAIN:** (1) Chọn ngày/log nguồn → (2) nhập before/after hoặc delta và lý do/evidence → (3) validate giới hạn, pháp nhân, kỳ khóa → (4) submit → (5) reviewer approve/reject → (6) nếu approved tạo quyết định công tách log → (7) reconcile payroll.
- **ALT/EXCEPTION:** Kỳ khóa => yêu cầu sửa kỳ/chênh lệch; self-approve => block; duplicate request => trả trạng thái cũ; reject phải có lý do. Mọi lỗi trước commit không tạo kết quả một phần; báo field và mã lỗi quy định.
- **POST/AUDIT:** Giữ source, decision, event và hậu quả chấm công; PR #3 chỉ có bản ghi decision, chưa áp dụng Attendance. Ghi actor, timestamp, pháp nhân, event/source, before/after khi có thay đổi, correlation ID.
- **Trace:** DE-VN-ATT-004..006; BR-VN-ATT-001; TC-ATT-002/005. Trạng thái triển khai xác nhận qua [bảng GAP](16-CODE-TO-DOC-GAP.md).

### 11. UC-VN-ATT-004 — Đăng ký và phê duyệt OT
- **Actor/trigger:** Employee, Manager, HR; khởi phát bởi tác vụ người dùng, sự kiện tích hợp hoặc lịch hiệu lực; xác thực và scope server-side.
- **PRE:** Có phân ca hiệu lực và chính sách OT theo loại ngày/đối tượng.
- **MAIN:** (1) Nhập khoảng OT và công việc → (2) xác định lịch/loại ngày → (3) kiểm tra giới hạn ngày/tháng/năm theo policy → (4) người có quyền duyệt → (5) đối chiếu giờ thực tế đã xác nhận → (6) phân đoạn qua 00:00/ngày lễ/ca đêm → (7) tính theo rule version.
- **ALT/EXCEPTION:** Trùng giờ, vượt giới hạn, thiếu xác nhận, chưa đủ hồ sơ => block/review; duyệt hồi tố chỉ khi policy cho phép. Mọi lỗi trước commit không tạo kết quả một phần; báo field và mã lỗi quy định.
- **POST/AUDIT:** Approved minutes/classification/source/version; không trả giờ không làm thực tế. Ghi actor, timestamp, pháp nhân, event/source, before/after khi có thay đổi, correlation ID.
- **Trace:** BR-VN-ATT-003/004; BR-OPS-OT; TC-OT-001/002/003. Trạng thái triển khai xác nhận qua [bảng GAP](16-CODE-TO-DOC-GAP.md).

### 12. UC-VN-ATT-005 — Đối soát và chốt bảng công
- **Actor/trigger:** HR, Manager, Payroll read-only; khởi phát bởi tác vụ người dùng, sự kiện tích hợp hoặc lịch hiệu lực; xác thực và scope server-side.
- **PRE:** Kỳ công thuộc pháp nhân, lịch/đơn nghỉ/OT/điều chỉnh đã đồng bộ.
- **MAIN:** (1) Tạo bảng công → (2) tổng hợp theo người/ngày → (3) hiện thiếu log/trùng/đơn chưa xử lý → (4) reconcile và soát ngoại lệ → (5) HR có quyền chốt → (6) tạo lock version/hash → (7) phát sự kiện cho payroll.
- **ALT/EXCEPTION:** Có exception chưa được chấp thuận => không chốt; reopen có approval và reason; sau payroll Paid dùng delta. Mọi lỗi trước commit không tạo kết quả một phần; báo field và mã lỗi quy định.
- **POST/AUDIT:** Công locked immutable theo version, có audit/snapshot. Ghi actor, timestamp, pháp nhân, event/source, before/after khi có thay đổi, correlation ID.
- **Trace:** BR-VN-ATT-005; BR-VN-PAY-001; TC-ATT-005;TC-PAY-001. Trạng thái triển khai xác nhận qua [bảng GAP](16-CODE-TO-DOC-GAP.md).

### 13. UC-VN-LEV-001 — Nộp đơn nghỉ phép
- **Actor/trigger:** Employee, delegated HR; khởi phát bởi tác vụ người dùng, sự kiện tích hợp hoặc lịch hiệu lực; xác thực và scope server-side.
- **PRE:** Nhân viên còn hiệu lực, có loại nghỉ, lịch và tuyến duyệt.
- **MAIN:** (1) Chọn loại phép/khoảng thời gian/nửa ngày → (2) hệ thống tính ngày/giờ theo ca và ngày nghỉ → (3) kiểm tra overlap, entitlement, balance, evidence → (4) xem ảnh hưởng công/lương → (5) submit vào tuyến duyệt.
- **ALT/EXCEPTION:** Số dư không đủ hoặc policy cho phép âm cần rule; trùng đơn => chặn; thiếu chứng cứ => pending bổ sung; kỳ khóa => nhánh adjustment. Mọi lỗi trước commit không tạo kết quả một phần; báo field và mã lỗi quy định.
- **POST/AUDIT:** Request có trạng thái, lịch sử và số ngày tính được; chưa ghi debit khi mới submit. Ghi actor, timestamp, pháp nhân, event/source, before/after khi có thay đổi, correlation ID.
- **Trace:** BR-VN-LEV-001; DE-VN-LEV-001..003; TC-LEV-001/005. Trạng thái triển khai xác nhận qua [bảng GAP](16-CODE-TO-DOC-GAP.md).

### 14. UC-VN-LEV-002 — Duyệt, từ chối, hủy nghỉ
- **Actor/trigger:** Manager, HR, Employee (cancel); khởi phát bởi tác vụ người dùng, sự kiện tích hợp hoặc lịch hiệu lực; xác thực và scope server-side.
- **PRE:** Request submitted, người duyệt có scope và không tự duyệt; số dư chưa xử lý trùng.
- **MAIN:** (1) Reviewer kiểm tra lịch và hồ sơ → (2) approve hoặc reject có reason → (3) trong transaction ghi ledger debit với source_key duy nhất → (4) cập nhật kết quả công/lịch → (5) gửi thông báo → (6) hủy hợp lệ ghi credit đảo một lần.
- **ALT/EXCEPTION:** Double click/retry không debit lần 2; kỳ đã Paid => không hoàn phép trực tiếp; cancel unauthorized/expired => block. Mọi lỗi trước commit không tạo kết quả một phần; báo field và mã lỗi quy định.
- **POST/AUDIT:** Ledger/balance khớp và audit đầy đủ; PR #3 ledger chưa nối LeaveRequest/AvailableLeave. Ghi actor, timestamp, pháp nhân, event/source, before/after khi có thay đổi, correlation ID.
- **Trace:** BR-VN-LEV-002/003; TC-LEV-002/004. Trạng thái triển khai xác nhận qua [bảng GAP](16-CODE-TO-DOC-GAP.md).

### 15. UC-VN-LEV-003 — Tính quyền lợi phép năm
- **Actor/trigger:** HR Policy Owner, payroll view; khởi phát bởi tác vụ người dùng, sự kiện tích hợp hoặc lịch hiệu lực; xác thực và scope server-side.
- **PRE:** Đủ hồ sơ, lịch sử công tác, loại lao động và rule entitlement có hiệu lực.
- **MAIN:** (1) Xác định nhóm đối tượng → (2) tính thời gian được tính là làm việc → (3) xử lý prorate/thâm niên/carryforward/expiry → (4) ghi accrual/adjustment theo source_key → (5) đối soát opening+credit-debit=closing.
- **ALT/EXCEPTION:** Thiếu rule hoặc lịch sử điều chuyển => flag và chặn chốt số dư; không hardcode 12 ngày cho mọi đối tượng. Mọi lỗi trước commit không tạo kết quả một phần; báo field và mã lỗi quy định.
- **POST/AUDIT:** Sổ phép đủ version và báo cáo giải thích được. Ghi actor, timestamp, pháp nhân, event/source, before/after khi có thay đổi, correlation ID.
- **Trace:** BR-VN-LEV-003; POLICY; TC-LEV-003/006. Trạng thái triển khai xác nhận qua [bảng GAP](16-CODE-TO-DOC-GAP.md).

### 16. UC-VN-PAY-001 — Tạo kỳ lương
- **Actor/trigger:** Payroll Specialist; khởi phát bởi tác vụ người dùng, sự kiện tích hợp hoặc lịch hiệu lực; xác thực và scope server-side.
- **PRE:** Pháp nhân/kỳ/nhóm nhân viên xác định; công locked, HĐ/rule có hiệu lực và quyền hợp lệ.
- **MAIN:** (1) Chọn company/period/pay_date → (2) preflight trùng, attendance lock, HĐ, rule version, PIT/BH → (3) lập danh sách người đủ điều kiện và lỗi → (4) tạo immutable input snapshot/source hash + run_id → (5) ghi Draft.
- **ALT/EXCEPTION:** Duplicate idempotency key trả run cũ; thiếu rule/HĐ/công => block, không tạo phiếu giả; thay đổi dữ liệu sau snapshot phải invalidation có kiểm soát. Mọi lỗi trước commit không tạo kết quả một phần; báo field và mã lỗi quy định.
- **POST/AUDIT:** Có payroll batch Draft và input snapshot/version; [SPEC] adapter vào Horilla chưa có. Ghi actor, timestamp, pháp nhân, event/source, before/after khi có thay đổi, correlation ID.
- **Trace:** BR-VN-PAY-001/006/007; TC-PAY-001/004/011. Trạng thái triển khai xác nhận qua [bảng GAP](16-CODE-TO-DOC-GAP.md).

### 17. UC-VN-PAY-002 — Tính thử lương theo kỳ
- **Actor/trigger:** Payroll Specialist; khởi phát bởi tác vụ người dùng, sự kiện tích hợp hoặc lịch hiệu lực; xác thực và scope server-side.
- **PRE:** Có snapshot hợp lệ; đủ biến, parameters và policy được approved; không dùng dữ liệu thật tại màn hình demo PR #3.
- **MAIN:** (1) Chọn run → (2) phân kỳ mức lương hiệu lực → (3) tính earning/gross → (4) tính BH NLĐ/DN riêng → (5) PIT theo residency/pay_date → (6) deduction/net → (7) trả từng dòng source/version, reconcile chênh lệch.
- **ALT/EXCEPTION:** Thiếu biến, chia 0, net âm, rule thiếu hoặc trùng => block với mã cụ thể; golden mismatch không thể approve ruleset; preview JSON hiện tại không ghi Payslip. Mọi lỗi trước commit không tạo kết quả một phần; báo field và mã lỗi quy định.
- **POST/AUDIT:** Kết quả explainable, cùng snapshot+rule cho cùng kết quả; version cố định. Ghi actor, timestamp, pháp nhân, event/source, before/after khi có thay đổi, correlation ID.
- **Trace:** BR-VN-PAY-002..007; TC-PAY-002/008/009/010/012. Trạng thái triển khai xác nhận qua [bảng GAP](16-CODE-TO-DOC-GAP.md).

### 18. UC-VN-PAY-003 — Phê duyệt và chốt lương
- **Actor/trigger:** Payroll Approver, Finance read; khởi phát bởi tác vụ người dùng, sự kiện tích hợp hoặc lịch hiệu lực; xác thực và scope server-side.
- **PRE:** Kỳ đã tính/đối soát, công khóa và policy approved; maker/checker tách.
- **MAIN:** (1) Xem reconciliation từng người → (2) xử lý hoặc chấp thuận ngoại lệ theo policy → (3) submit → (4) approver kiểm tra hash/tổng/tỷ lệ → (5) approve → (6) freeze output, phát hành phiếu theo quyền.
- **ALT/EXCEPTION:** Self approval, source hash đã đổi, thiếu dữ liệu legal, âm Net không có ngoại lệ => block; reject trả về Draft bằng version mới, không sửa silently. Mọi lỗi trước commit không tạo kết quả một phần; báo field và mã lỗi quy định.
- **POST/AUDIT:** Phiếu lương bất biến ở mức được duyệt; audit approver/decision. Ghi actor, timestamp, pháp nhân, event/source, before/after khi có thay đổi, correlation ID.
- **Trace:** BR-VN-PAY-007/008; BR-VN-SEC-001; TC-PAY-003/006. Trạng thái triển khai xác nhận qua [bảng GAP](16-CODE-TO-DOC-GAP.md).

### 19. UC-VN-PAY-004 — Ghi nhận kết quả chi trả
- **Actor/trigger:** Finance, payment reconciler; khởi phát bởi tác vụ người dùng, sự kiện tích hợp hoặc lịch hiệu lực; xác thực và scope server-side.
- **PRE:** Bảng lương approved; có file chi trả được kiểm soát, mã đối soát ngân hàng.
- **MAIN:** (1) Export bank file có checksum → (2) ghi nhận bank acknowledgment theo giao dịch → (3) match ref/số tiền/người nhận → (4) xử lý hàng rejected/partial → (5) đánh dấu từng payslip Paid khi xác nhận → (6) đóng toàn kỳ chỉ khi không còn pending.
- **ALT/EXCEPTION:** Export file không đồng nghĩa Paid; thiếu một giao dịch không Paid toàn bộ; retry acknowledgment idempotent; sai số tiền phải điều tra. Mọi lỗi trước commit không tạo kết quả một phần; báo field và mã lỗi quy định.
- **POST/AUDIT:** Có bank reference, pay_date thực tế, proof và immutable paid totals. Ghi actor, timestamp, pháp nhân, event/source, before/after khi có thay đổi, correlation ID.
- **Trace:** BR-VN-PAY-008; RPT-VN-010; TC-RPT-004;TC-PAY-007. Trạng thái triển khai xác nhận qua [bảng GAP](16-CODE-TO-DOC-GAP.md).

### 20. UC-VN-PAY-005 — Truy lĩnh/truy thu kỳ sau
- **Actor/trigger:** Payroll Specialist, Approver; khởi phát bởi tác vụ người dùng, sự kiện tích hợp hoặc lịch hiệu lực; xác thực và scope server-side.
- **PRE:** Phiếu kỳ gốc đã chốt hoặc Paid; có source event thay đổi hợp lệ và lý do.
- **MAIN:** (1) Chọn payslip gốc → (2) định vị dữ liệu thay đổi và version hiệu lực → (3) tính giá trị đáng lẽ có/giá trị đã trả → (4) tạo delta, phân loại thuế/BH theo rule và ngày liên quan → (5) submit/approve → (6) đưa delta vào kỳ mới.
- **ALT/EXCEPTION:** Không sửa số tiền phiếu Paid; duplicate source_id => không ghi điều chỉnh lần 2; thiếu chính sách hồi tố => chặn. Mọi lỗi trước commit không tạo kết quả một phần; báo field và mã lỗi quy định.
- **POST/AUDIT:** Có delta liên kết original_payslip, kỳ gốc và kỳ ghi nhận, audit. Ghi actor, timestamp, pháp nhân, event/source, before/after khi có thay đổi, correlation ID.
- **Trace:** BR-VN-PAY-008; DE-VN-PAY-007; TC-PAY-003/010. Trạng thái triển khai xác nhận qua [bảng GAP](16-CODE-TO-DOC-GAP.md).

### 21. UC-VN-RPT-001 — Báo cáo và xuất dữ liệu
- **Actor/trigger:** HR, Payroll, Finance, auditor; khởi phát bởi tác vụ người dùng, sự kiện tích hợp hoặc lịch hiệu lực; xác thực và scope server-side.
- **PRE:** Có quyền report + data_scope + field_scope trên dataset được yêu cầu.
- **MAIN:** (1) Chọn mẫu/kỳ/bộ lọc → (2) server scope dataset → (3) che trường nhạy cảm trước serialize → (4) tổng hợp/đối soát → (5) xuất PDF/XLSX có version/hash → (6) audit người xuất, mục đích, số bản ghi.
- **ALT/EXCEPTION:** Cross-tenant ID/query => 403/404 chống enumeration; dữ liệu công thức CSV => escape; không có quyền field => không trả raw JSON. Mọi lỗi trước commit không tạo kết quả một phần; báo field và mã lỗi quy định.
- **POST/AUDIT:** File chỉ chứa dữ liệu đúng phạm vi, giữ lịch sử export. Ghi actor, timestamp, pháp nhân, event/source, before/after khi có thay đổi, correlation ID.
- **Trace:** BR-VN-RPT-001; BR-VN-SEC-002; TC-RPT-001..003;TC-SEC-002/004. Trạng thái triển khai xác nhận qua [bảng GAP](16-CODE-TO-DOC-GAP.md).

### 22. UC-VN-SEC-001 — Cấp/thu hồi quyền theo pháp nhân
- **Actor/trigger:** Security Admin, privileged approver; khởi phát bởi tác vụ người dùng, sự kiện tích hợp hoặc lịch hiệu lực; xác thực và scope server-side.
- **PRE:** Có định danh và quyền cấp quyền độc lập; đối tượng/role/scope có trong danh mục.
- **MAIN:** (1) Chọn người dùng/role → (2) chọn company, department, field rights, thời hạn → (3) kiểm tra privilege escalation và self-grant → (4) phê duyệt với quyền nhạy cảm → (5) kích hoạt grant → (6) audit và revoke token khi thu hồi.
- **ALT/EXCEPTION:** Không cấp cross-tenant vô hạn; quyền hết hạn tự vô hiệu; superuser kỹ thuật không mặc định xem lương; emergency access có quy trình riêng. Mọi lỗi trước commit không tạo kết quả một phần; báo field và mã lỗi quy định.
- **POST/AUDIT:** Quyền hữu hiệu được kiểm tra tại API/queryset/field/export. Ghi actor, timestamp, pháp nhân, event/source, before/after khi có thay đổi, correlation ID.
- **Trace:** BR-VN-ORG-001; BR-VN-SEC-001/002; TC-SEC-001..008. Trạng thái triển khai xác nhận qua [bảng GAP](16-CODE-TO-DOC-GAP.md).

### 23. UC-VN-OFF-001 — Chấm dứt hợp đồng/Offboarding
- **Actor/trigger:** HR, Manager, Finance, IT; khởi phát bởi tác vụ người dùng, sự kiện tích hợp hoặc lịch hiệu lực; xác thực và scope server-side.
- **PRE:** Có employment/contract active, phân loại căn cứ nghỉ và ngày hiệu lực.
- **MAIN:** (1) Tiếp nhận đề nghị → (2) kiểm tra báo trước/điều kiện chấm dứt → (3) lập checklist bàn giao/tài sản/công nợ → (4) chốt công/đơn nghỉ/quyền lợi cuối kỳ → (5) tính và duyệt nghĩa vụ thanh toán → (6) revoke quyền theo ngày hiệu lực → (7) archive có retention.
- **ALT/EXCEPTION:** Thiếu tài sản/settlement => case unresolved theo policy, không xóa hồ sơ; kỳ lương Paid => adjustment; không thu hồi token => security incident. Mọi lỗi trước commit không tạo kết quả một phần; báo field và mã lỗi quy định.
- **POST/AUDIT:** Nhân viên chuyển Offboarded và lịch sử nguyên vẹn; payroll/IT nhận sự kiện. Ghi actor, timestamp, pháp nhân, event/source, before/after khi có thay đổi, correlation ID.
- **Trace:** BR-VN-SEC-001/002; BR-VN-PAY-008; TC-SEC-005;TC-OFF-001. Trạng thái triển khai xác nhận qua [bảng GAP](16-CODE-TO-DOC-GAP.md).

## 3. Hợp đồng giao dịch giữa các Use Case (E2E)
| Luồng liên thông | Nguồn sự thật | Gate trước khi chuyển | Hậu quả nếu thất bại |
|---|---|---|---|
| EMP→CON | Employee ID, company assignment | Nhân viên Active và pháp nhân khớp | HĐ giữ Draft |
| CON→ATT | HĐ/assignment hiệu lực, work calendar version | Không chồng lấn lịch/ca trái policy | Gắn exception, không tạo công giả |
| ATT/LEV/OT→PAY | Bảng công LOCKED + ledger/OT decision | Không thiếu quyết định trọng yếu, snapshot hash ổn | Chặn batch preflight, ghi lỗi per employee |
| PAY→BANK | Approved payslip/snapshot | Tổng lương đối soát; Finance được quyền | Không đổi sang Paid |
| CON/OFF→SEC | Ngày nghỉ/điều chuyển có quyết định | Thu hồi vai trò/refresh token đúng ngày | Incident và retry revocation |
| RuleSet→PAY | VNRuleSet approved, đúng company/code/effective date | Golden cases đã đối soát, rule không xung đột | Fail closed, không dùng bản Draft |

## 4. Ma trận bắt buộc áp cho tất cả 23 UC
- **Rights:** read/create/update/submit/approve/reject/cancel/export/close phân theo role + tenant + manager hierarchy + field scope + delegation effective dates.
- **Concurrency:** sử dụng revision/row lock cho approve/close/ledger/payroll và compare-and-swap trạng thái. Hai actor duyệt đồng thời chỉ một tác vụ thành công.
- **Idempotency:** event integration/import và các thao tác bút toán phải nhận source key, trả kết quả cũ khi retry hợp lệ.
- **Retry/rollback:** lỗi network sau commit trả resource id để caller truy vấn; không thực hiện duplicate side effects; job retry qua outbox có correlation id.
- **Audit:** đối tượng, record id, actor, action, old/new (masked), source, timestamp, reason, request id, policy/rule version; bảo toàn immutable lịch sử.
- **UAT:** positive, required/blank, max length, invalid enum, wrong tenant, wrong role, invalid state, duplicate, race, timezone/date boundary, policy missing, post-Paid, import/export.
- **DoR:** chỉ chuyển READY khi mỗi bước MAIN/ALT được ánh xạ endpoint/màn hình và test; nếu còn quyết định chính sách mở ghi \`BLOCKED_BY_POLICY\` ở đầu UC.

## 5. Quy trình phê duyệt đặc tả
BA kiểm tra tính hoàn chỉnh và trace; HR duyệt hồ sơ/HĐ/công/phép; Kế toán duyệt đối soát lương; Pháp chế duyệt rule pháp luật/hiệu lực; Security duyệt quyền và vault; QA duyệt bộ tình huống ranh giới. **Không đặt trạng thái VERIFIED/IMPLEMENTED chỉ vì đã tạo file tài liệu.**

Tham chiếu: [BRD](01-BRD-CHUC-NANG-VA-QUY-TRINH.md), [SRS](02-SRS-USE-CASE-VA-BUSINESS-RULE.md), [Validation](10-FIELD-LEVEL-VALIDATION-MATRIX.md), [Workflow](13-WORKFLOW-STATE-TRANSITIONS.md).
