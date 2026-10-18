# Tham chiếu thuế TNCN tiền lương cư trú 2026

Chỉ hỗ trợ **kiểm thử đối soát độc lập**, không là cấu hình tự bật để trả lương, khai thuế, quyết toán hoặc nộp tờ khai.

- Căn cứ Luật Thuế TNCN **109/2025/QH15** và văn bản hợp nhất **112/VBHN-VPQH** ngày 20/05/2026 (sửa đổi bởi **09/2026/QH16**). Quy định về tiền lương cư trú áp dụng từ **kỳ tính thuế năm 2026**.
- Mức giảm trừ bản thân 15.500.000 VND/tháng; người phụ thuộc 6.200.000 VND/tháng.
- Biểu thuế tháng lũy tiến 5 bậc: đến 10 triệu 5%; trên 10–30 triệu 10%; trên 30–60 triệu 20%; trên 60–100 triệu 30%; trên 100 triệu 35%.
- Nguồn [Văn bản hợp nhất](https://thuvienphapluat.vn/van-ban/Thue-Phi-Le-Phi/Van-ban-hop-nhat-112-VBHN-VPQH-2026-Luat-Thue-thu-nhap-ca-nhan-706726.aspx), [Bộ Tài chính giới thiệu luật](https://nief.mof.gov.vn/tin-tuc/noi-dung-chinh-cua-luat-thue-thu-nhap-ca-nhan-so-109-2025-qh15-11929.html).
- `vn_payroll/reference_pit_2026.py`: kiểm tra thuật toán, nhận **tiền lương chịu thuế đã phân loại trước**, bảo hiểm được khấu trừ, số người phụ thuộc đã xác minh, giảm trừ khác được duyệt. Không tự suy từ Gross Horilla; không áp dụng cho người không cư trú, thuế thu nhập kinh doanh, quy tắc ưu đãi hay khấu trừ đa kỳ.
- Số liệu tiền lương/các khoản miễn và giảm trừ vẫn phải được HR, kế toán thuế, pháp chế kiểm tra; bộ tham chiếu chưa đủ điều kiện phát hành.

## Ma trận trường hợp phải bổ sung trước production
- Thu nhập chịu thuế so với Gross, OT ưu đãi, khoản miễn, công tác phí, tiền nhà, hiện vật.
- Người không cư trú, hợp đồng ngắn hạn, thời điểm trả thu nhập, truy lĩnh, lương ngoại tệ.
- Người phụ thuộc có hiệu lực đầu/cuối tháng, xác minh trùng, thay đổi cư trú.
- Giảm trừ theo chứng từ hợp lệ và hiệu lực pháp lý, quyết toán năm / khấu trừ tháng.
- Lương giữa kỳ thay đổi luật và phiếu thưởng; kiểm tra mẫu biểu & hóa đơn/eTax thực tế.

Bất kỳ ca nào chưa xác minh: **NO-GO**.
