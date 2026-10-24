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
2. **Đội** vào trang chủ → nhập **mã đội, tên đội** → form có 7 ô: **Phiếu trả lời** (`.docx`, bắt buộc),
   **Bài 1 → Bài 5** (mỗi ô 3 tệp `.py` của A, B, C) và **Hidden Challenge** (3 tệp `.py`, không bắt buộc) → Nộp.
   Tệp được lưu **giữ nguyên tên đội đặt** (đề chấm điểm cả quy cách tên `<MaDoi>_<A/B/C>_BaiN.py`); quá 3 tệp
   một ô, sai loại tệp hoặc trùng tên tệp thì nộp lỗi.
   Trang của đội **chỉ có quyền nộp**. Lúc nộp chỉ kiểm tra **thông tin đội**:
   - Mã đội, tên đội nhập vào phải **khớp** với ô Mã đội, Tên đội trong phiếu (không phân biệt hoa/thường,
     khoảng trắng thừa); phiếu phải đọc được. **Đúng và đủ → "Nộp thành công"**.
   - Sai/thiếu → **"Nộp lỗi"** kèm lý do, đội nộp lại. Lần nộp lỗi vẫn được lưu để admin thấy, nhưng **không chấm**.
   Lỗi trong bài làm (cú pháp, đặt sai tên tệp, thiếu bài...) **không báo cho đội** - chỉ admin thấy ở mục "Kiểm tra
   định dạng", và bị trừ điểm khi chấm. Đội không xem được điểm hay trang nào khác; mọi trang `/admin` yêu cầu
   đăng nhập, `/docs`, `/openapi.json` đã tắt.
3. **Không chấm tự động khi nộp.** Mỗi đội **chỉ chấm lần nộp thành công cuối cùng**. Ở trang tổng quan, mỗi đội có
   **nút "Chấm" riêng ở cuối dòng**; hoặc bấm **"Chấm các bài chưa chấm"** để chấm hết một lượt. Đội nộp lại sau khi
   đã chấm thì về "Chưa chấm", chờ admin chấm lại.
4. **Bấm vào một đội** → trang chi tiết: **số lần nộp** và **bảng lịch sử** (mỗi lần: thời gian, nộp thành công/nộp lỗi
   kèm lý do, bản nào được chấm, điểm). Bấm một dòng để xem lần nộp đó: file, mã nguồn, phiếu, kiểm tra định dạng;
   với bản được chấm còn có điểm theo bài (A, B, C, Checkpoint, điểm tệp), lý do mất/trừ điểm, Hidden Challenge,
   test ẩn, output, và nút **Duyệt đạt / Không đạt** cho từng phần, điểm tệp từng bài và code Hidden
   (điểm tính lại ngay, không chạy lại code).
5. **Xếp hạng**: tổng điểm → hoàn thành Hidden Challenge → thời điểm nộp bản được chấm sớm hơn.
   Tải CSV để công bố.

## Deploy (miễn phí): nộp bài trên Google Apps Script, chấm trên Vercel

> Hướng dẫn từng bước: [../HUONG_DAN_DEPLOY.md](../HUONG_DAN_DEPLOY.md)

Web chọn nơi lưu theo biến môi trường (`kho.py`):

| Biến môi trường | Nơi lưu | Dùng khi |
|---|---|---|
| `APPS_SCRIPT_URL`, `APPS_SCRIPT_KHOA` | Apps Script (`../apps_script/`) giữ trang nộp bài + Google Drive; web này chỉ admin + chấm, kéo bài qua API của Apps Script | **Deploy Vercel (khuyên dùng)** |
| `GOOGLE_CLIENT_ID/SECRET`, `GOOGLE_REFRESH_TOKEN`, `DRIVE_FOLDER_ID` | Web tự lưu lên Drive bằng OAuth (`kho_drive.py`, lấy token bằng `lay_token_drive.py`) | Phương án thay thế, cần cấu hình Google Cloud |
| (không có) | SQLite + `web/du_lieu/` | Chạy trên máy cá nhân / VPS |

Trên Vercel (có biến `VERCEL`), web **chấm ngay khi admin bấm** (không chạy nền): nút **Chấm** từng đội chấm xong
trong vài giây đến vài chục giây; **Chấm các bài chưa chấm** chấm tối đa ~4 phút mỗi lượt (giới hạn 300 giây/request
của Vercel), còn đội chưa chấm thì bấm lại. Mỗi lần chạy code tối đa 5 giây (`CHAM_THOI_GIAN`).

## Lưu ý

- Đội không đăng nhập nên ai biết mã đội + tên đội (và có phiếu ghi đúng) cũng nộp thay được; dùng trong phòng
  thi/mạng nội bộ. Trang admin giữ toàn bộ lịch sử các lần nộp để đối chiếu khi có tranh chấp.
- Code của thí sinh được chạy trên máy chủ (tiến trình riêng, có giới hạn thời gian). Khi mở ra
  Internet nên chạy web trong container không có mạng, giới hạn RAM/CPU, và đổi mật khẩu admin.
- Sao lưu thư mục `web/du_lieu/` sau cuộc thi.
