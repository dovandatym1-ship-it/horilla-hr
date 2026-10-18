# VN-HRM | Đặc tả tính lương, thuế TNCN và bảo hiểm tại Việt Nam
**Mã:** VNHRM-PAY-05 · **Phiên bản:** 1.0 · **Ngày:** 17/10/2026 · **Trạng thái:** Dự thảo; **chưa được phép dùng để chi trả thực tế khi thiếu phê duyệt luật/rule**.
**Code AS-IS:** `payroll/methods/payroll_run.py`, `payslip_calc.py`, `tax_calc.py`, `contributions.py`, `batch_run.py`, `payroll/models/models.py`, `payroll/models/payroll_batch.py`, `payroll/tax_packs.py`. Các chức năng xây mới ghi TO-BE.

## 1. Bản chất một kỳ lương
**Pay period** = kỳ số liệu công/lương; **Pay date** = ngày chi thực tế; **Tax recognition date** = thời điểm thu nhập chịu thuế theo pháp luật; ba ngày/kỳ này không được đồng nhất. Bảng lương theo pháp nhân, người lao động, hợp đồng/mức lương có hiệu lực, công/nghỉ/OT đã duyệt, rule set pháp lý và chính sách nội bộ đã duyệt.

Đầu ra phải phân biệt:
1. **Thu nhập:** lương cơ bản theo ngày/giờ, phụ cấp chịu/không chịu thuế theo phân loại, thưởng, hoa hồng, làm thêm, các khoản một lần.
2. **Giảm trừ tiền lương:** đi làm thiếu công, nghỉ không lương, ứng lương, khoản khấu trừ khác có căn cứ; không nhầm với giảm trừ thuế.
3. **Nghĩa vụ NLĐ:** phần bảo hiểm NLĐ chịu, PIT khấu trừ, các khoản khấu trừ phù hợp.
4. **Nghĩa vụ doanh nghiệp:** phần bảo hiểm doanh nghiệp chịu, chi phí khác; **không** trừ vào Net của nhân viên.
5. **Net:** số tiền thực lĩnh sau các khoản hợp pháp; Employer Cost tính riêng.

## 2. Chuỗi tính toán và hợp đồng dữ liệu
```text
Hợp đồng, cơ cấu lương (effective date)
      + Lịch, công, phép, OT đã khóa
      + Khoản thu nhập một lần / truy lĩnh-truy thu
      + Quy tắc thuế, bảo hiểm, lương tối thiểu đã DUYỆT
                            ↓
Chụp snapshot nguồn theo nhân viên - kỳ - pháp nhân
                            ↓
Lương theo kỳ → Earnings → Gross
                            ↓
Xác định nền tính BH và loại đối tượng → NLĐ đóng / DN đóng
                            ↓
Phân loại taxable earning → Các khoản được trừ → Taxable Income
                            ↓
Tính PIT theo đối tượng cư trú, kỳ và biểu tương ứng
                            ↓
Khấu trừ không thuế còn lại → Net
                            ↓
Soát lỗi và đối chiếu → Phê duyệt → Phát hành → Thanh toán
```
Tính **Decimal** cho các bước có tiền, định nghĩa `rounding_mode` và thứ tự làm tròn theo pháp chế/kế toán; giữ số trung gian cho kiểm tra, chỉ xuất `amount_vnd` theo đơn vị đồng sau chốt. Không dùng `float` làm chuẩn mới dù lõi Horilla vẫn có `FloatField`.

## 3. Phiếu lương mẫu cần giải thích được
Thông tin đầu phiếu: mã người lao động, pháp nhân, kỳ công, kỳ lương, ngày thanh toán, hợp đồng/version, rule version, số ngày/giờ công chuẩn và được hưởng lương, OT được duyệt.

| Nhóm | Dòng bắt buộc theo trường hợp | Rule bắt buộc |
|---|---|---|
| Base | Lương theo HĐ, prorate vào/ra giữa kỳ | Căn cứ lương/giờ, ngày công chuẩn và loại kỳ |
| Earnings | OT theo phân loại, thưởng, phụ cấp, hoàn trả | Mỗi dòng có taxability/insurance-ability độc lập |
| Gross | Tổng thu nhập kỳ trước khấu trừ | Bằng tổng dòng earning theo rule |
| Insurance NLĐ | BHXH, BHYT, BHTN, khác nếu áp dụng | Căn cứ đóng và trần/tỷ lệ theo phiên bản |
| PIT | Thu nhập chịu thuế, giảm trừ, PIT tạm khấu trừ | Theo đối tượng cư trú/thời điểm chi trả |
| Other deductions | Tạm ứng, bồi hoàn, khoản khác được duyệt | Kiểm tra giới hạn/điều kiện hợp pháp |
| Net | Số thực lĩnh | Gross − các khoản NLĐ phải trừ ± điều chỉnh được duyệt |
| Employer cost | BH phần DN và chi phí doanh nghiệp | Không cộng vào net |
| Reconciliation | Giữa các dòng, số chuyển khoản, kỳ trước | Chênh lệch có lý do |

## 4. Bộ quy tắc thuế TNCN 2026 đã đối chiếu nguồn nhà nước
**Nguồn:** Luật Thuế TNCN số 109/2025/QH15 (hiệu lực 01/07/2026; các quy định về thu nhập tiền lương/công của cá nhân cư trú áp dụng từ kỳ tính thuế 2026), Nghị định 253/2026/NĐ-CP, Nghị quyết 110/2025/UBTVQH15.

**Giảm trừ tháng đối với cá nhân cư trú có đủ điều kiện:** bản thân **15.500.000 VND**, mỗi người phụ thuộc **6.200.000 VND** trong kỳ tính thuế 2026. Không áp giảm trừ cho tất cả lao động không cư trú; phải xác minh tình trạng cư trú, hồ sơ, nơi đăng ký người phụ thuộc, tháng được tính.

**Biểu thuế lũy tiến từng phần đối với thu nhập tính thuế/tháng (đơn vị triệu VND):**

| Bậc | Phần thu nhập tính thuế/tháng | Thuế suất |
|---|---|---:|
| 1 | Đến 10 | 5% |
| 2 | Trên 10 đến 30 | 10% |
| 3 | Trên 30 đến 60 | 20% |
| 4 | Trên 60 đến 100 | 30% |
| 5 | Trên 100 | 35% |

Công thức ví dụ ở mức *thu nhập tính thuế tháng đã được xác định hợp lệ* T = 35 triệu: `10 × 5% + 20 × 10% + 5 × 20% = 3,5 triệu VND`. Đây là **test cho thuật toán biểu thuế**, không phải ví dụ quyết toán lương thực tế vì chưa đưa dữ liệu gross và BH vào.

**BR-PIT-001** nhận diện cá nhân cư trú/không cư trú và tình trạng hợp đồng theo ngày trả thu nhập; trạng thái chưa xác định ⇒ không tính thuế như cư trú theo suy đoán.  
**BR-PIT-002** mỗi loại thu nhập gán `tax_category` và `exempt_basis` theo hiệu lực; khoản không chịu thuế không được mặc định giống khoản không tính đóng BH.  
**BR-PIT-003** lấy các khoản đóng bảo hiểm được trừ và các khoản giảm trừ hợp lệ *trước khi* tính thu nhập tính thuế, tránh trừ hai lần.  
**BR-PIT-004** người phụ thuộc từ hồ sơ và thời gian được tính theo quy định; phân biệt tạm tính trong năm và quyết toán, không suy từ số con.  
**BR-PIT-005** lưu tax bracket version, tên văn bản, thời điểm công bố/hiệu lực, cấu hình và căn cứ phân loại, bảng giải thích số thuế cho từng bậc.  
**BR-PIT-006** thu nhập nhận ở nhiều nơi, ủy quyền quyết toán, điều chỉnh hồi tố cần quy trình riêng và phê duyệt; không giả định system có đủ dữ liệu ngoài doanh nghiệp.  
**BR-PIT-007** Gross-to-Net có gross-up/thuế trả thay theo hướng dẫn riêng, không dùng đảo công thức tuyến tính nếu có bậc thuế hoặc thu nhập trả thay.

Nguồn kiểm tra:
- https://xaydungchinhsach.chinhphu.vn/chi-tiet-bieu-thue-thu-nhap-ca-nhan-luy-tien-tung-phan-119260327091407544.htm
- https://xaydungchinhsach.chinhphu.vn/quy-dinh-giam-tru-gia-canh-119260703144038062.htm
- https://xaydungchinhsach.chinhphu.vn/thue-thu-nhap-ca-nhan-doi-voi-thu-nhap-tu-tien-luong-tien-cong-119260703141953435.htm
- https://chinhphu.vn/?classid=1&docid=218684&pageid=27160&typegroupid=4

## 5. Mức lương tối thiểu 2026 và kiểm tra HĐ
Theo Nghị định 293/2025/NĐ-CP (áp dụng 01/01/2026):
| Vùng | Tháng (VND) | Giờ (VND) |
|---|---:|---:|
| I | 5.310.000 | 25.500 |
| II | 4.730.000 | 22.700 |
| III | 4.140.000 | 20.000 |
| IV | 3.700.000 | 17.800 |

Địa bàn xác định theo **nơi hoạt động của người sử dụng lao động**, cần mapping đúng địa danh và phụ lục có hiệu lực; khi nhân viên chuyển địa điểm cần lịch sử ngày áp dụng. Mức tối thiểu tháng/giờ và nguyên tắc quy đổi phải tuân thủ chính văn bản, không chỉ lấy lương danh nghĩa chia tùy tiện.

Nguồn: https://xaydungchinhsach.chinhphu.vn/nghi-dinh-so-293-2025-nd-cp-quy-dinh-muc-luong-toi-thieu-doi-voi-nguoi-lao-dong-lam-viec-theo-hop-dong-lao-dong-119251110172808433.htm

## 6. Bảo hiểm bắt buộc
**Không đóng cứng một bộ tỷ lệ BH cho mọi nhân viên** cho đến khi Kế toán/Pháp chế xác nhận toàn bộ căn cứ 2026, trần và đối tượng. Thiết kế `InsuranceEnrollment` có BHXH, BHYT, BHTN riêng, thời điểm tham gia, mã số BHXH, tình trạng lao động và căn cứ đóng từng loại. Các đối tượng như người lao động Việt Nam/người nước ngoài, hợp đồng với thời lượng khác nhau, thai sản/tạm hoãn, nghỉ dài hạn, điều chuyển giữa pháp nhân cần nhánh quyết định.

- **BR-INS-001:** xác định đủ điều kiện BH theo luật và tình trạng HĐ/đối tượng/kỳ hiệu lực; thiếu dữ liệu bắt buộc ⇒ flag hoặc block trước khi Paid.
- **BR-INS-002:** nền tính BH tách Gross, basic salary và cấu phần lương; khoản phụ cấp có/không tính đóng phải do rule phê duyệt.
- **BR-INS-003:** `employee_amount` và `employer_amount` luôn tách; giới hạn mức trần/sàn kiểm tra theo phiên bản và vùng khi phù hợp.
- **BR-INS-004:** tăng/giảm BH theo tháng hiệu lực và chính sách có căn cứ; không tự giả định nhân viên nghỉ ngày nào cũng ngừng đóng.
- **BR-INS-005:** tính thử và đối soát danh sách đóng BH, tổng theo pháp nhân; xuất báo cáo phục vụ rà soát, **không** coi export là đã gửi cơ quan BH.
- **BR-INS-006:** phân biệt khoản BH được trừ khỏi thu nhập tính thuế với khoản đóng của doanh nghiệp; ghi ref chứng từ.

**Quan ngại pháp lý:** trang vbpl.vn cho Luật BHXH 41/2024/QH15 hiển thị trạng thái “hết hiệu lực toàn bộ” từ 01/01/2026 trong khi các nguồn khác vẫn dẫn luật sửa đổi/hợp nhất. Đây là xung đột tra cứu phải được Pháp chế xác minh văn bản hợp nhất và điều khoản hiệu lực trước khi bật luật trong production. Không coi một kết quả tra cứu không nhất quán là cơ sở để bỏ toàn bộ chế độ.

## 7. Cấu hình LegalRuleVersion
Đề xuất các trường: `rule_code`, `jurisdiction=VN`, `law_reference`, `source_url`, `company_id` nullable, `employee_category`, `pay_component_category`, `effective_from`, `effective_to`, `approved_at`, `approved_by`, `status=draft/review/approved/retired`, `rate_or_formula`, `rounding_policy`, `rule_hash`, `reason_for_change`. Trùng khoảng hiệu lực trong cùng phạm vi/priority thì từ chối publish. Tiền lương phải snapshot version đã approved **theo thời điểm nghiệp vụ**, không lấy bản mới nhất.

## 8. Ngoại lệ và đối soát
| Ngoại lệ | Hành vi mong muốn |
|---|---|
| Không có hợp đồng hiệu lực | Không tính lương chính thức; nêu nhân viên và ngày thiếu |
| HĐ điều chỉnh giữa kỳ | Chia khoảng theo hiệu lực, đối soát lương chuẩn |
| Phát sinh OT sau chốt công | Không lặng lẽ sửa snapshot; tạo quy trình công và lương điều chỉnh |
| Thu nhập âm do truy thu | Chặn/điều chỉnh có lý do theo giới hạn hợp pháp |
| BH chưa rõ điều kiện | Flag; không áp tỷ lệ mặc định cho mọi người |
| Tình trạng cư trú thiếu | Block phần thuế và hiển thị yêu cầu xác nhận |
| Chạy lại cùng `run_id` | Idempotent, không tạo lương đôi |
| Ngân hàng xác nhận thiếu dòng | Chưa đánh dấu hoàn tất toàn kỳ, đối soát từng người |
| Rule thay đổi sau Paid | Lưu rule cũ với phiếu; tạo delta có ref và phép tính tái lập |
| Kỳ thuế khác kỳ công | Tách thời điểm tính thuế/ngày chi trả |

## 9. Test Cases đặc trưng
**TC-PAY-001:** công chưa khóa ⇒ lỗi `ATTENDANCE_NOT_LOCKED`. **TC-PAY-002:** cùng input + legal version + Decimal rounding ⇒ cùng gross/Net/hash. **TC-PIT-001:** T = 35 triệu ⇒ PIT biểu lũy tiến 3,5 triệu ở ví dụ thuật toán (không có giảm trừ khác). **TC-PIT-002:** người phụ thuộc được đăng ký giữa năm ⇒ đúng tháng hợp lệ, không khấu trừ sai kỳ. **TC-PIT-003:** người phụ thuộc chưa chứng thực ⇒ chỉ tính theo trạng thái/rule được duyệt, hiển thị lý do. **TC-INS-001:** phần DN không trừ Net. **TC-INS-002:** điều chuyển/đổi căn cứ đóng giữa kỳ ⇒ phân kỳ đúng và đối soát được. **TC-PAY-003:** bảng lương Paid ⇒ không sửa dòng tiền; adjustment kỳ sau. **TC-PAY-004:** chọn nhầm pháp nhân ⇒ 403, không lộ dữ liệu. **TC-PAY-005:** hợp đồng ghi 2 mức cùng hiệu lực ⇒ block/giải quyết trước calculate. **TC-PAY-006:** tính từ snapshot sau tháng vẫn giống thời điểm Paid. **TC-PAY-007:** batch partial failure không “Paid” giả toàn bộ.

## 10. Điều kiện Go/No-Go
**No-Go** nếu chưa có bộ golden payroll kiểm toán độc lập, văn bản/phiên bản được HR/Kế toán/Pháp chế duyệt, 100% case pháp nhân bị ngăn truy cập, khóa dữ liệu Paid, đối soát Net/Bank, backup & rollback thực nghiệm. Tài liệu chỉ chốt yêu cầu; không chứng nhận ứng dụng đã tuân thủ.


## 11. Phụ lục Payroll v1.1 — Quy tắc thực thi, kết nối và cổng pháp lý
**Phân biệt 2 workflow:** (a) cấu hình/kiểm thử/duyệt \`VNRuleSet\` với \`VNPayRule\` ở PR #3 — đã có model, service, Admin preview và unit tests viết; (b) kỳ lương chính thức có Contract/Attendance/Leave/Tax/Insurance snapshot/Payslip/Bank/Paid — **chưa tích hợp adapter** từ engine mới vào \`payroll_run.py\` và quy trình chi trả Horilla.

**Contract dữ liệu bắt buộc để tích hợp:** company, employee, pay_period, pay_date, tax_recognition_date, contract/effective wage version, attendance_lock_version, approved OT/leave source, residency/dependent eligibility version, income taxability/insurance-ability tags, rule_set version, rounding mode, source hash, dòng earning/insurance NLĐ+DN/tax/deduction/net và reconciliation. Phép tính chính thức chỉ nhận tham số luật đã phê duyệt; test independent golden trường hợp ranh giới.

**Gate:** Không đưa tính lương chính thức vào Paid nếu thiếu (1) pháp nhân và scope, (2) HĐ/công/OT/phép có hiệu lực/chốt, (3) policy thuế-BH/OT có căn cứ và ngày hiệu lực, (4) Golden Cases độc lập của Kế toán, (5) đối soát gross/net/phiếu ngân hàng, (6) khóa Paid immutable và audit, (7) UAT pháp lý.

**Lưu ý tính cập nhật luật:** các con số và văn bản ở mục 4–6 là phiên bản tài liệu đang chờ người có trách nhiệm xác nhận hiệu lực/diễn giải từng đối tượng và kỳ tính; không tự động tạo tỷ lệ/tax rule production từ bảng này. Nếu có văn bản sửa đổi, phân loại/ưu tiên theo legal register mục 06 và Decision Log, ghi rõ nguồn chính thức.

Chi tiết [RuleSet field validation](10-FIELD-LEVEL-VALIDATION-MATRIX.md), [Payroll workflow](13-WORKFLOW-STATE-TRANSITIONS.md), [test oracle](15-TRACEABILITY-UAT-MATRIX.md), [integration GAP](16-CODE-TO-DOC-GAP.md).
