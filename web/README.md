# Web nộp bài & chấm bài – Vòng 1 Olympic AI UNETI 2026

Dùng engine chấm trong `../cham_diem`. Dữ liệu (SQLite + bài nộp) lưu ở `web/du_lieu/`.

## Chạy

```powershell
cd "d:\DHKL16A2HN\Research assistant\Hằng anh\hacktathon\web"
pip install -r requirements.txt        # nếu máy chưa có
python app.py
```

- Trang nộp bài (đội thi, không cần đăng nhập): http://127.0.0.1:8000
- Trang admin: http://127.0.0.1:8000/admin – tài khoản **admin**, mật khẩu **admin123**
  (đổi bằng biến môi trường `ADMIN_TAI_KHOAN`, `ADMIN_MAT_KHAU` nếu cần).

Cho máy khác trong mạng LAN truy cập: `$env:HOST = "0.0.0.0"` trước khi chạy (đổi cổng bằng `$env:PORT`).

## Quy trình

1. **Admin** đăng nhập → đặt hạn nộp, mở nộp bài. Có thể thêm trước danh sách đội (`MÃ_ĐỘI,Tên đội`)
   để có sẵn tên; không bắt buộc.
2. **Đội** vào trang chủ → nhập mã đội (+ tên đội) → form có 6 ô: **Phiếu trả lời** (chỉ nhận `.docx`,
   bắt buộc) và **Bài 1 → Bài 5** (mỗi ô một file `.py`/`.ipynb`) → Nộp. Chọn sai loại file thì báo lỗi ngay
   và server không nhận lần nộp. File được lưu với tên chuẩn theo ô (`<MÃ>_Bai1.py`, `<MÃ>_PhieuTraLoi.docx`).
   Đội chưa có trong danh sách được tạo tự động. Trang của đội **chỉ có quyền nộp**; nộp xong chỉ nhận thông báo:
   - **Nộp lỗi** (sai loại file, thiếu phiếu, phiếu không đọc được/sai mẫu): bài **bị từ chối, không chấm điểm**,
     đội nộp lại. Lần nộp lỗi vẫn được lưu để admin thấy (nhãn đỏ "Nộp lỗi · không chấm", kèm lý do và file đã gửi);
     nếu đội có lần nộp hợp lệ trước đó thì điểm vẫn tính theo lần hợp lệ đó.
   - **Đã nhận nhưng có vấn đề** (file chạy lỗi, nộp nhầm ô, thiếu bài, phiếu còn ô trống, mã đội trong phiếu khác):
     nên sửa và nộp lại trước hạn.
   - **Nộp thành công**.
   Đội không xem được điểm, kết quả chấm hay bất kỳ trang nào khác; mọi trang `/admin` đều yêu cầu đăng nhập,
   và trang tài liệu API tự sinh (`/docs`, `/openapi.json`) đã tắt. Lần nộp sau thay thế lần trước.
3. **Không chấm tự động khi nộp** (lúc nộp chỉ kiểm tra nhẹ, không chạy code - nhiều đội nộp cùng lúc không quá tải).
   Admin bấm **"Chấm các bài chưa chấm"** (hoặc "Chấm bài này" ở trang từng đội) khi muốn, vd sau khi hết hạn nộp.
   Bài được chấm nền lần lượt, mỗi đội vài giây; chỉ lần nộp hợp lệ mới nhất của mỗi đội được chấm.
   Đội nộp lại sau khi đã chấm thì về trạng thái "Chưa chấm", chờ admin chấm lại.
4. **Admin** xem từng đội: điểm theo bài, lý do mất/trừ điểm, test ẩn, output, mã nguồn, phiếu.
   Phần "Chờ duyệt" → bấm **Duyệt đạt / Không đạt**, điểm tính lại ngay (không chạy lại code).
   Bấm **Chấm lại** nếu cần chạy lại.
5. **Xếp hạng**: tổng điểm → giải đúng Hidden Challenge → thời điểm nộp phiếu có thông điệp đúng sớm nhất.
   Tải CSV để công bố.

## Lưu ý

- Đội không đăng nhập nên ai biết mã đội cũng nộp thay được; dùng trong phòng thi/mạng nội bộ, và đối chiếu
  mã đội ghi trong phiếu Word (trang kết quả và trang admin đều cảnh báo khi không khớp).
- Code của thí sinh được chạy trên máy chủ (tiến trình riêng, có giới hạn thời gian). Khi mở ra
  Internet nên chạy web trong container không có mạng, giới hạn RAM/CPU, và đổi mật khẩu admin.
- Sao lưu thư mục `web/du_lieu/` sau cuộc thi.
