# Horilla HRM — Bộ tài liệu chuẩn hóa và Việt Nam hóa nghiệp vụ

**Dự án:** [dovandatym1-ship-it/horilla-hr](https://github.com/dovandatym1-ship-it/horilla-hr)  
**Baseline đã phân tích:** Horilla nhánh `2.0`, commit `fad3c73f212bd9a591b743024a1e6870e01f0f20`, `horilla/__version__.py` = `2.1.8`.  
**Phiên bản bộ tài liệu:** 1.0 · **Ngày:** 17/10/2026 · **Trạng thái:** DRAFT — phân tích mã nguồn tĩnh, chưa UAT, chưa phê duyệt pháp chế và chưa sửa mã vận hành.

## 1. Danh sách tài liệu — đọc theo trình tự

| Thứ tự | Tài liệu | Mục đích / người đọc |
|---|---|---|
| 00 | [Quy ước và thuật ngữ](00-QUY-UOC-VA-THUAT-NGU.md) | Từ vựng tiếng Việt, naming, định dạng, vai trò, phân biệt AS-IS/TO-BE/LAW/POLICY |
| 01 | [BRD: chức năng và quy trình](01-BRD-CHUC-NANG-VA-QUY-TRINH.md) | BA/HR: mục tiêu, GAP, chuỗi quy trình đầu-cuối, trạng thái và vai trò |
| 02 | [SRS: Use Case và Business Rules](02-SRS-USE-CASE-VA-BUSINESS-RULE.md) | BA/Dev/QA: hành vi hệ thống, rule có mã, nhánh lỗi, NFR |
| 03 | [Từ điển dữ liệu & ánh xạ code](03-TU-DIEN-DU-LIEU-VA-ANH-XA-CODE.md) | Dev/DBA/BA: entity, field, ràng buộc, nhạy cảm, hiệu lực, migration |
| 04 | [Ca làm, chấm công, OT, nghỉ phép](04-CHAM-CONG-CA-LAM-NGHI-PHEP.md) | HR Ops/QA: công chuẩn, log, chỉnh công, phép ledger, chốt công |
| 05 | [Tính lương, TNCN, bảo hiểm](05-TINH-LUONG-THUE-BAO-HIEM.md) | Payroll/Finance/Dev: chuỗi tính, snapshot, rule 2026, đối soát |
| 06 | [Sổ căn cứ pháp lý và quyết định](06-DANG-KY-PHAP-LY-VA-POLICY-DECISION-LOG.md) | Pháp chế/HR/Payroll: nguồn chính thống, effective date, vấn đề BLOCKED |
| 07 | [An ninh, phân quyền, báo cáo, tích hợp](07-BAO-MAT-PHAN-QUYEN-BAO-CAO.md) | Security/Dev/QA: RBAC, tenant, PII, report, file bank |
| 08 | [UAT, traceability & roadmap](08-UAT-TRACEABILITY-ROADMAP.md) | PM/BA/Dev/QA: backlog 20 feature, mapping code/test, gating |
| 09 | [Giao diện, màn hình và thông điệp tiếng Việt](09-CHUAN-HOA-GIAO-DIEN-VA-THONG-DIEP-VI.md) | BA/UX/Dev: menu, form, datagrid, workflow action, lỗi và thông báo |
| Tổng quan | [Phân tích GAP và kế hoạch gốc](HORILLA_HRM_VIET_NAM_2026_ANALYSIS_PLAN.md) | Đọc nhanh hiện trạng/kiến trúc/lộ trình; khi có khác biệt, áp dụng bản chi tiết đã kiểm soát |

## 2. Quy tắc áp dụng và thứ tự ưu tiên
1. **Không đồng nghĩa đã triển khai:** tài liệu là kế hoạch/yêu cầu; `vn_hrm`, `vn_payroll`, `vn_reports` là app ĐỀ XUẤT, chưa có trong code.
2. **Nguồn sự thật về AS-IS:** luôn đọc code đúng branch/commit đã ghi; module “có trong repo” không đồng nghĩa nghiệp vụ đã đáp ứng luật Việt Nam.
3. **Nguồn sự thật về luật:** văn bản chính thức và sổ pháp lý 06, kèm ý kiến Pháp chế/Kế toán ký duyệt; trường hợp hiệu lực xung đột **BLOCKED**, không tự đoán.
4. **Nguồn sự thật về dữ liệu và hành vi:** STD-00 → BRD-01 → SRS-02 → DATA-03 → bộ đặc tả miền 04–07 → TC ở 08. Mâu thuẫn phải tạo Decision/Change Request trước khi code.
5. **Mỗi dòng backlog:** liên kết Feature → UC → BR → dữ liệu → file Horilla/adapter → test → biên bản nghiệm thu, có owner và version.
6. **Không sửa kỳ đã Paid:** thay đổi hồi tố qua phiên bản nghiệp vụ và delta kỳ sau có phê duyệt.

## 3. Kiểm tra trước khi phát triển
- [ ] Chạy Horilla 2.0 với test suite, Docker và tạo baseline số lượng lỗi/coverage.
- [ ] Khảo sát công ty mẫu: pháp nhân, nhân sự, lịch công, ca, phép, loại thu nhập, HĐ, quy chế lương.
- [ ] Chốt Decision Log, đặc biệt BHXH 2026, ngày trả lương và cấu hình OT/phép.
- [ ] Chuẩn hóa danh mục địa giới/mức lương theo mốc hiệu lực và nguồn được duyệt.
- [ ] Chạy golden payroll so với bảng tính đã được Kế toán phê duyệt trước bất kỳ chi trả nào.
- [ ] Kiểm tra chống đọc chéo pháp nhân, PII, xuất và link file nhạy cảm.
- [ ] Duyệt UAT, rollback và phương án khôi phục trước khi production.

## 4. Về nội dung tiếng Việt
Toàn bộ tài liệu nghiệp vụ dùng tiếng Việt có dấu, nhất quán các khái niệm: **Nhân viên**, **Hợp đồng lao động**, **Bảng công**, **Kỳ lương**, **Lương Gross/Net**, **Bảo hiểm xã hội**, **Thuế TNCN**, **Người phụ thuộc**, **Phê duyệt**, **Chốt kỳ**. Chuỗi giao diện tiếng Việt phải được trích xuất và dịch theo i18n chuẩn trong một PR code khác; hiện PR này **chỉ bổ sung/chỉnh tài liệu**.
