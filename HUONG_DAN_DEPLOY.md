# Hướng dẫn deploy: nộp bài trên Google Apps Script, chấm trên Vercel

Mọi thứ **miễn phí, không cần thẻ, không cần Google Cloud**. Làm một lần, khoảng 30 phút.

```
Sinh viên ──► Trang nộp bài (Google Apps Script) ──lưu──► Google Drive của bạn
                        ▲
                        │ API có khóa bí mật
Admin ──────► Web chấm (Vercel) ── kéo bài qua Apps Script ──► chấm ──► lưu kết quả vào Drive
```

- **Apps Script** (thư mục `apps_script/`): trang nộp bài, kiểm tra mã đội + tên đội khớp phiếu, lưu bài vào Drive.
- **Vercel** (thư mục `web/`, `cham_diem/`, `api/`): trang admin, chấm bài, duyệt tay, xếp hạng.
- Sinh viên **không cần đăng nhập**. Bài nằm trong Google Drive của bạn.

Cần chuẩn bị: 1 tài khoản **Gmail** (chứa bài nộp), 1 tài khoản **GitHub** của bạn, máy có **Git**.

---

## Phần A. Trang nộp bài trên Google Apps Script

1. Mở **https://script.google.com** bằng Gmail sẽ chứa bài → **New project** (Dự án mới).
   Bấm tên "Untitled project" ở góc trên → đổi thành `Olympic AI - Nộp bài`.
2. **Code.gs**: xóa hết nội dung có sẵn, mở file `apps_script/Code.gs` trong dự án này, chép toàn bộ, dán vào → **Ctrl+S**.
3. **Index.html**: bấm dấu **+** cạnh chữ *Files* → **HTML** → đặt tên `Index` (không gõ .html) →
   xóa nội dung có sẵn, dán toàn bộ file `apps_script/Index.html` → **Ctrl+S**.
4. **Múi giờ**: bấm biểu tượng bánh răng **Project Settings** (cột trái) → *Time zone*: chọn
   **(GMT+07:00) Bangkok, Hanoi, Jakarta** (hoặc Ho Chi Minh). Hạn nộp tính theo múi giờ này.
5. **Cài đặt lần đầu**: quay lại **Editor** (biểu tượng `< >`) → trên thanh công cụ, ô chọn hàm chọn
   **caiDatLanDau** → bấm **Run**.
   - Hiện *Authorization required* → **Review permissions** → chọn Gmail của bạn.
   - Hiện *"Google hasn't verified this app"* → **Advanced** → **Go to Olympic AI - Nộp bài (unsafe)** → **Allow**
     (đây là script của chính bạn).
   - Ô **Execution log** bên dưới hiện 2 dòng:
     ```
     Thư mục lưu bài: https://drive.google.com/drive/folders/...
     APPS_SCRIPT_KHOA (dán vào Vercel): 3f9a...
     ```
     → **chép khóa** (dãy ký tự sau dấu `:`) ra Notepad.
   - Mở Google Drive sẽ thấy thư mục **OlympicAI_Vong1** (bên trong có `bai_nop`). **Đừng xóa / đổi tên.**
6. **Deploy**: góc trên phải bấm **Deploy** → **New deployment** → bấm bánh răng cạnh *Select type* → **Web app**:
   - *Description*: `v1`
   - *Execute as*: **Me** (Gmail của bạn)
   - *Who has access*: **Anyone** (Bất kỳ ai)
   - → **Deploy** → chép **Web app URL** (dạng `https://script.google.com/macros/s/.../exec`) ra Notepad.
7. Mở link đó bằng **cửa sổ ẩn danh** (không đăng nhập) → phải thấy trang **Nộp bài Vòng 1**.

> **Sửa Code.gs / Index.html sau này**: sửa xong → **Deploy → Manage deployments** → bấm bút chì ✏️ →
> *Version*: **New version** → **Deploy**. Link `/exec` giữ nguyên. (Chỉ Ctrl+S thì trang thật chưa đổi.)

## Phần B. Đưa code lên GitHub (repo của bạn)

1. Vào **https://github.com/new** → *Repository name*: `olympic-ai` → chọn **Private** → không tick "Add a README"
   → **Create repository**.
2. PowerShell:
   ```powershell
   cd "d:\DHKL16A2HN\Research assistant\Hằng anh\hacktathon"
   git rm -r --cached web/du_lieu
   git add .
   git commit -m "Web cham bai: Vercel + Apps Script"
   git remote set-url origin https://github.com/<TEN_GITHUB_CUA_BAN>/olympic-ai.git
   git push -u origin master
   ```
   - `git rm` gỡ dữ liệu chạy thử (có khóa phiên) khỏi Git, file trên máy vẫn còn. Báo *"did not match"* thì bỏ qua.
   - Lần đầu push, cửa sổ đăng nhập GitHub hiện ra → **Sign in with your browser**.
3. Trên GitHub kiểm tra có `api/`, `web/`, `cham_diem/`, `apps_script/`, `vercel.json` và **không có** `web/du_lieu`.

> Repo chứa thư mục `data/` (đáp án) nên phải để **Private**. File `.vercelignore` đã chặn `data/`, `bai_giai_mau/`,
> `web/du_lieu/` khỏi bản deploy.

## Phần C. Web chấm trên Vercel

1. **https://vercel.com/signup** → **Continue with GitHub** → gói **Hobby** (miễn phí).
2. **Add New…** → **Project** → chọn repo `olympic-ai` → **Import**
   (không thấy repo: **Adjust GitHub App Permissions** → cho phép repo `olympic-ai`).
3. *Framework Preset*: **Other**, *Root Directory*: `./` → mở **Environment Variables**, thêm 4 biến:

   | Key | Value |
   |---|---|
   | `APPS_SCRIPT_URL` | Web app URL ở bước A.6 (kết thúc bằng `/exec`) |
   | `APPS_SCRIPT_KHOA` | khóa ở bước A.5 |
   | `ADMIN_MAT_KHAU` | mật khẩu admin bạn tự đặt (đừng dùng `admin123`) |
   | `PHIEN_BI_MAT` | chuỗi ngẫu nhiên, tạo bằng `python -c "import secrets; print(secrets.token_hex(32))"` |

4. **Deploy** → đợi 1–2 phút → **Continue to Dashboard** → link web ở mục **Domains** (`https://...vercel.app`).

## Phần D. Kiểm tra trước khi dùng thật

1. Mở `https://...vercel.app/admin` → tài khoản `admin`, mật khẩu `ADMIN_MAT_KHAU` → thấy trang **Các đội thi**
   và dòng *Link gửi các đội để nộp bài* trỏ tới link Apps Script. (Mở `https://...vercel.app/` cũng tự chuyển sang trang nộp.)
2. Mở trang nộp bài (link Apps Script), nộp thử bộ mẫu `bai_giai_mau\2_python_gop\`:
   Mã đội `MAU`, Tên đội `Đội mẫu`, ô Phiếu: `MAU_PhieuTraLoi_Vong1.docx`, ô Bài 1–5: `MAU_Bai1.py`…`MAU_Bai5.py`
   → **Nộp bài** → phải hiện **"Nộp thành công"**.
3. Google Drive → `OlympicAI_Vong1/bai_nop/` → có thư mục `MAU_...` chứa 6 file.
4. Trang admin (tải lại) → dòng **MAU** → **Chấm** → đợi trang tải lại → **25/25**.
5. Nộp thử sai tên đội (`Đội khác`) → phải báo **NỘP LỖI**; trang admin hiện lần đó là *Nộp lỗi*.

## Phần E. Ngày thi

1. Trang admin → **Hạn nộp** (giờ Việt Nam) → tick **Mở nộp bài** → **Lưu**. Trang nộp bài Apps Script áp dụng ngay.
2. Gửi các đội **link Apps Script** (hoặc link Vercel – tự chuyển hướng). Đội nộp: mã + tên đội **giống hệt phiếu**,
   1 phiếu Word + file bài từng ô.
3. Hết giờ → admin bấm **Chấm các bài chưa chấm** (mỗi lượt tối đa ~4 phút, còn đội chưa chấm thì bấm lại),
   hoặc **Chấm** từng đội ở cuối dòng.
4. Duyệt tay phần **Chờ duyệt** → **Bảng xếp hạng** → **Tải CSV**.
5. Sao lưu: Drive → chuột phải thư mục `OlympicAI_Vong1` → **Tải xuống**.

## Cập nhật sau này

- Sửa web chấm (`web/`, `cham_diem/`): `git add . ; git commit -m "..." ; git push` → Vercel tự deploy lại.
- Sửa trang nộp bài (`apps_script/`): dán lại vào script.google.com → **Deploy → Manage deployments → ✏️ → New version**.
- Đổi biến môi trường trên Vercel → **Deployments** → bản mới nhất → **⋯ → Redeploy**.

## Lỗi thường gặp

Xem log Vercel: project → **Logs**. Xem log Apps Script: script.google.com → **Executions** (cột trái).

| Hiện tượng | Cách sửa |
|---|---|
| Vercel báo lỗi 500, log *"Chạy trên Vercel cần cấu hình nơi lưu bài"* | Thiếu `APPS_SCRIPT_URL` / `APPS_SCRIPT_KHOA` → thêm → **Redeploy** |
| Log *"Apps Script không trả về JSON"* | `APPS_SCRIPT_URL` sai (phải là link **/exec**, không phải /dev) hoặc *Who has access* chưa là **Anyone** |
| Log *"Apps Script: Sai khóa API"* | `APPS_SCRIPT_KHOA` không khớp khóa ở bước A.5 (chạy lại `caiDatLanDau` để xem) |
| Trang nộp bài báo *"Hệ thống chưa được cài đặt"* | Chưa chạy `caiDatLanDau` (bước A.5) |
| Sửa Code.gs mà trang nộp bài không đổi | Chưa tạo **New version** khi deploy |
| Sinh viên thấy *"Hệ thống đang bận, bài chưa được nhận"* | Apps Script đang quá tải (giới hạn ~30 lượt cùng lúc) → đợi vài giây, nộp lại |
| Log Vercel có `ModuleNotFoundError` / không thấy template | Cấu hình đóng gói Vercel cần chỉnh – gửi log để sửa |
| Mọi phần đều "Chạy lỗi" khi chấm | Môi trường Vercel khác máy – gửi log + trang chi tiết một đội để sửa |

## Lưu ý

- Apps Script giới hạn khoảng **30 lượt chạy cùng lúc** cho một tài khoản: nếu rất nhiều đội bấm nộp cùng một giây,
  vài đội có thể phải bấm lại. Trang nộp bài sẽ báo rõ để đội nộp lại.
- Đầu trang nộp bài có dòng nhỏ của Google *"Ứng dụng này được tạo bởi người dùng Google Apps Script"* – bình thường.
- Khóa `APPS_SCRIPT_KHOA` cho phép đọc/ghi dữ liệu bài nộp – chỉ dán vào Vercel, không gửi ai, không đưa lên Git.
  Lộ khóa: vào Apps Script → Project Settings → *Script Properties* → xóa `KHOA_API` → chạy lại `caiDatLanDau`
  (sinh khóa mới) → cập nhật trên Vercel.
- Code thí sinh chạy trên Vercel không đọc được các biến bí mật (web đã lọc biến môi trường).
- Chạy thử trên máy không cần Google: `cd web` → `python app.py` → http://127.0.0.1:8000 (dùng SQLite như cũ).
