# VN-HRM | Sổ đăng ký căn cứ pháp lý và quyết định nghiệp vụ
**Mã:** VNHRM-LEGAL-06 · **Phiên bản:** 1.0 · **Kiểm tra ngày:** 17/10/2026 · **Trạng thái:** Dự thảo; cần Legal/Payroll Owner phê duyệt trước khi dùng các tham số để trả lương.

## 1. Quy ước độ tin cậy và phê duyệt
**VERIFIED-SOURCE:** đã đối chiếu nguồn nhà nước, chứng minh sự tồn tại/hiệu lực và nội dung nêu trong tài liệu. **NEEDS-LEGAL-REVIEW:** có sửa đổi, diễn giải, ngoại lệ hoặc xung đột hiệu lực chưa giải quyết. **POLICY-OPEN:** phụ thuộc nội quy/quy chế/thỏa ước/HĐ. **RETIRED:** không dùng rule cho kỳ mới, giữ lại để tái lập bảng lương quá khứ.

## 2. Sổ văn bản trọng tâm
| ID | Văn bản/nguồn | Tác động HRM | Trạng thái |
|---|---|---|---|
| LAW-VN-001 | Bộ luật Lao động 45/2019/QH14; hướng dẫn NĐ 145/2020/NĐ-CP và sửa đổi | HĐ, thử việc, thời giờ, OT, nghỉ phép, chấm dứt | NEEDS-LEGAL-REVIEW (văn bản bị sửa đổi một phần) |
| LAW-VN-002 | Luật BHXH 41/2024/QH15 và VBHN/sửa đổi liên quan | Đối tượng, căn cứ, tham gia và chế độ | NEEDS-LEGAL-REVIEW (trạng thái nguồn không nhất quán) |
| LAW-VN-003 | Luật Việc làm 74/2025/QH15 hiệu lực 01/01/2026 | BHTN, tham gia và nghĩa vụ | VERIFIED-SOURCE cho văn bản/hiệu lực; tỷ lệ cần soát hướng dẫn |
| LAW-VN-004 | Luật Thuế TNCN 109/2025/QH15; NĐ 253/2026/NĐ-CP hiệu lực 01/07/2026 | Thu nhập, biểu thuế, người phụ thuộc, thời điểm chi trả | VERIFIED-SOURCE với giá trị thuế ở PAY-05 |
| LAW-VN-005 | Nghị quyết 110/2025/UBTVQH15 áp dụng kỳ tính thuế 2026 | Mức giảm trừ gia cảnh | VERIFIED-SOURCE |
| LAW-VN-006 | NĐ 293/2025/NĐ-CP hiệu lực 01/01/2026 | Lương tối thiểu theo vùng, tháng/giờ, địa điểm | VERIFIED-SOURCE |
| LAW-VN-007 | Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15 và NĐ 356/2025/NĐ-CP cùng hiệu lực 01/01/2026 | Thu thập, mục đích, xử lý hồ sơ nhân sự, quyền dữ liệu | VERIFIED-SOURCE cho hiệu lực; chi tiết cần DPO rà soát |
| LAW-VN-008 | Luật sửa đổi BHYT 51/2024/QH15 và văn bản liên quan | Đối tượng và căn cứ BHYT | NEEDS-LEGAL-REVIEW |
| LAW-VN-009 | Quy định địa giới hành chính hiện hành từ 2025 và các văn bản sửa đổi | Danh mục tỉnh/xã/phường/đặc khu, giữ lịch sử | POLICY-OPEN nguồn dữ liệu authoritative và sync |

**Nguồn chính thống đã tra cứu:**
- 45/2019/QH14: https://vbpl.vn/nganhangnhanuoc/Pages/ivbpq-thuoctinh.aspx?ItemID=139264
- 41/2024/QH15: https://vbpl.vn/tw/Pages/vbpq-thuoctinh.aspx?ItemID=175027
- 74/2025/QH15: https://vbpl.vn/bolaodong/Pages/ivbpq-thuoctinh.aspx?ItemID=179273
- 109/2025/QH15: https://vbpl.vn/tw/Pages/vbpq-thuoctinh.aspx?ItemID=187045
- 253/2026/NĐ-CP: https://chinhphu.vn/?classid=1&docid=218684&pageid=27160&typegroupid=4
- 110/2025/UBTVQH15: https://xaydungchinhsach.chinhphu.vn/nghi-quyet-110-2025-ubtvqh15-dieu-chinh-muc-giam-tru-gia-canh-cua-thue-thu-nhap-ca-nhan-119251110101313787.htm
- 293/2025/NĐ-CP: https://xaydungchinhsach.chinhphu.vn/nghi-dinh-so-293-2025-nd-cp-quy-dinh-muc-luong-toi-thieu-doi-voi-nguoi-lao-dong-lam-viec-theo-hop-dong-lao-dong-119251110172808433.htm
- 91/2025/QH15: https://vbpl.vn/tw/Pages/vbpq-thuoctinh.aspx?ItemID=179252
- 356/2025/NĐ-CP: https://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID=187276

## 3. Đặc biệt về BHXH — không diễn giải quá mức
Nguồn CSDL quốc gia `ItemID=175027` hiển thị **“Hết hiệu lực toàn bộ” từ 01/01/2026**, đồng thời tồn tại nội dung hợp nhất/sửa đổi và các tài liệu tiếp tục sử dụng Luật 41/2024. Tài liệu hiện tại **không kết luận** toàn bộ chế độ BHXH hết giá trị thực thi hay tự cho phép bỏ BHXH. **DEC-LEGAL-001** yêu cầu pháp chế đối chiếu văn bản hợp nhất áp dụng tại kỳ, quy định chuyển tiếp, văn bản hướng dẫn thu BHXH, BHYT, BHTN năm 2026 và ghi memo có dẫn chứng trước khi duyệt `LR-VN-INS-2026-v1`.

## 4. Bảng điều khiển phiên bản rule và mốc hiệu lực
| Rule | Scope | Giá trị/nguồn | Phê duyệt |
|---|---|---|---|
| LR-VN-PIT-2026-v1 | Cá nhân cư trú tiền lương/công | 5 bậc; 5%, 10%, 20%, 30%, 35%; ranh giới 10/30/60/100 triệu đồng/tháng | Pending Legal + Payroll |
| LR-VN-PIT-DED-2026-v1 | Giảm trừ gia cảnh | Bản thân 15,5 triệu/tháng; 1 NPT 6,2 triệu/tháng | Pending Legal + Payroll |
| LR-VN-MINWAGE-2026-v1 | Vùng I/II/III/IV | 5,31/4,73/4,14/3,70 triệu đồng/tháng, có mức giờ | Pending Legal + HR |
| LR-VN-INS-2026-v1 | Đối tượng BH theo HĐ/loại lao động | **Không có tỷ lệ/trần mặc định** trong tài liệu vì chưa hoàn tất legal reconciliation | BLOCKED |
| LR-VN-OT-2026-v1 | Phân loại OT, night, ngày lễ | Phải mapping Điều luật, phương thức tính, nhóm làm việc và mẫu test | BLOCKED |
| LR-VN-LEAVE-2026-v1 | Phép/năm, thâm niên, nghỉ chế độ | Cấu hình theo nhóm, trường hợp, quy chế | Pending HR + Legal |

**Mẫu record chuẩn:** `rule_id, topic, authority, law_number, official_url, law_effective_from, rule_effective_from, rule_effective_to, applicable_employee_type, applicability_predicate, priority, parameters_json, change_reason, reviewed_by, approved_by, approved_at, status, test_case_refs`.

## 5. Decision Log chưa được đóng
| Mã | Câu hỏi phải trả lời | Chủ quyết định | Tác động nếu bỏ trống |
|---|---|---|---|
| DEC-LEGAL-001 | BHXH 2026: văn bản hợp nhất nào, điều khoản chuyển tiếp, tỷ lệ/trần/đối tượng? | Pháp chế + Payroll | Chặn tính BH |
| DEC-LEGAL-002 | Các khoản phụ cấp nào chịu thuế, đóng BH? | Payroll + Pháp chế | Sai Gross/Net, thiếu căn cứ |
| DEC-LEGAL-003 | Phép năm cho nhóm nghề, phép tăng theo thâm niên, nghỉ chuyển năm? | HR + Pháp chế | Sai quyền lợi |
| DEC-LEGAL-004 | Công chuẩn ca ngày, ca đêm, xoay ca; OT ban đêm và trùng ngày nghỉ? | HR + Pháp chế | Sai công/OT |
| DEC-LEGAL-005 | Phương pháp làm tròn từng dòng/tổng và xử lý tiền lẻ VND? | Kế toán | Không đối soát |
| DEC-LEGAL-006 | Ngày trả lương, kỳ thuế và thu nhập truy lĩnh? | Payroll + Thuế | Sai kỳ khấu trừ |
| DEC-LEGAL-007 | Lưu dữ liệu CCCD, người phụ thuộc, sức khỏe bao lâu, ai có quyền? | DPO + Pháp chế | Rủi ro dữ liệu |
| DEC-LEGAL-008 | Phân quyền phê duyệt bảng lương và mở khóa công? | Ban điều hành + HR | Thiếu SoD |
| DEC-LEGAL-009 | Nguồn danh mục mã tỉnh/xã/đặc khu authoritative và cách giữ địa chỉ cũ? | BA + Data Owner | Sai vùng lương và hồ sơ |
| DEC-LEGAL-010 | Loại hình NV lao động nước ngoài và cách xác định cư trú? | HR + Pháp chế | Sai BH/thuế |

## 6. Quy trình kiểm soát cập nhật pháp luật
Tạo issue `REG-CHANGE` khi có văn bản mới → thu thập URL, số, ban hành, hiệu lực, đối tượng → Pháp chế phân tích thay thế/chuyển tiếp → BA lập GAP và tác động các module → Payroll/HR xác nhận công thức với golden cases → test song song kỳ cũ/kỳ mới → Approver duyệt → publish version tương lai → xác minh sản xuất → retire version cũ (không xóa). Mọi nguồn không xác nhận được phải thể hiện `BLOCKED` thay vì ghi “đúng pháp luật”.

**Lưu ý:** Thông tin tra cứu phản ánh thời điểm 17/10/2026. Khi triển khai hoặc sử dụng thực tế phải kiểm tra biến động pháp lý và thẩm định lại.
