# Engine chấm tự động – Vòng 1 Olympic AI UNETI 2026

Yêu cầu: Python 3.9+ (dùng `ast.unparse`), không cần thư viện ngoài.

```bash
python cham.py <thu_muc_bai_nop_cua_doi> --phieu phieu.json --json ket_qua.json
```

BE có thể gọi CLI rồi đọc `ket_qua.json`, hoặc import trực tiếp: `from cham import cham_doi`.

## Cách tính điểm mỗi bài (tối đa 5)

1. **Điểm theo phiếu** (tối đa 4): mỗi mục A, B, C, Checkpoint (K + mảnh khóa) ghi đúng được 1.
2. **Trừ theo code**: mục phiếu ghi đúng nhưng code không chứng minh được thì bị trừ, kèm nhóm lý do:
   không nộp code · code không đúng yêu cầu đề · code lỗi · không in ra kết quả · in ra đáp án sai ·
   chưa xác minh được (chờ người chấm).
   Checkpoint bị trừ khi output code của bất kỳ phần A/B/C nào sai hoặc không có (lỗi, không in,
   không nộp, chưa xác minh). Phiếu điền sai hoặc code vi phạm yêu cầu đề mà output vẫn đúng thì
   chỉ mất điểm phần đó, không kéo theo Checkpoint.
3. **Nộp đủ** (1): tìm thấy code của cả 3 phần.

Nguyên tắc: **phiếu là căn cứ chấm, code để xác thực**. Phiếu ghi sai thì mục đó không có điểm,
kể cả khi code đúng (báo cáo vẫn ghi rõ "code đúng nhưng phiếu sai").

## Đội tổ chức file tùy ý

Mỗi phần một file, gộp A/B/C của một bài, gộp cả 5 bài, trộn `.py` và `.ipynb`, tên file bất kỳ
đều chấm được. Phần nào nằm ở file nào được nhận ra bằng **dữ liệu đề cho xuất hiện trong code**
(1956, 2026, "UNETI2026", danh sách cạnh...); tên file chỉ là gợi ý khi không thấy dữ liệu.

Với file gộp (`phan_tach.py`):
- Vùng code của từng phần = lát cắt dữ liệu: các câu lệnh dùng (trực tiếp hoặc gián tiếp) dữ liệu
  của phần đó + hàm nó gọi. Kiểm tra tĩnh chạy trên vùng này, nên `sort` hợp lệ ở Bài 5 không
  làm Bài 2 bị trừ.
- Khi chạy, mỗi phần được tách ra thành chương trình riêng (bỏ code của phần khác) để lỗi của
  thành viên này không làm hỏng điểm thành viên khác; không tách được thì chạy cả file.
- Kết quả được đọc bằng cách so sánh output trước/sau khi thay dữ liệu, nên không phụ thuộc
  định dạng in.

## Cách xác thực một phần A/B/C (1 điểm)

1. **Nạp code**: `.py` đọc nguyên văn; `.ipynb` chỉ lấy ô code, **bỏ output đã lưu** (chỉ dùng để đối chiếu,
   phát hiện output bị sửa tay), vô hiệu hóa magic `%`/`!`, biểu thức cuối ô được in như Jupyter.
2. **Kiểm tra tĩnh** (AST): ràng buộc của đề – không `sort/sorted`, không `Counter`, không `str(year)`,
   phải có vòng lặp, phải dùng dict, không `sklearn`...
3. **Chạy thật** trong tiến trình riêng (timeout, thư mục tạm, không stdin). Đọc dòng `A = <giá trị>`,
   nếu không có thì lấy số cuối cùng được in (kèm cảnh báo).
4. **Test ẩn**: tìm literal dữ liệu đề cho trong code (nhận nhiều hình dạng: list, chuỗi nhiều dòng,
   dict kề, X/nhãn tách riêng...), thay bằng dữ liệu khác, chạy lại và so với hàm tham chiếu của BTC.
   Code hard-code hoặc thuật toán sai sẽ trượt ở bước này.

Trạng thái: `DAT` (1đ) · `KHONG_DAT` (0đ, có `ly_do`) · `CAN_REVIEW` (có `canh_bao`, người chấm xem lại;
nếu không tìm thấy dữ liệu đề trong code thì tạm 0đ vì không chứng minh được code tự tính).

## Notebook (.ipynb)

- Chạy từng ô theo thứ tự như Jupyter; output đã lưu chỉ dùng để đối chiếu (phát hiện sửa tay).
- Vô hiệu hóa cú pháp riêng của Jupyter: `%magic`, `!lệnh`, `x = !lệnh`, `obj?`; `%%time`,
  `%%timeit`, `%%capture` giữ lại thân ô; ô `%%bash`/`%%html`/`%%writefile` bị bỏ qua.
- Có sẵn `display()`, `get_ipython()` và `google.colab` giả (code viết trên Colab chạy được).
- Ô bị lỗi: ghi cảnh báo rồi chạy tiếp; hết lượt thì chạy lại các ô lỗi một lần (thí sinh chạy
  sai thứ tự). Phần đó vẫn phải qua test ẩn mới có điểm, và bị đánh dấu `CAN_REVIEW`.
  Muốn chấm nghiêm như "Restart & Run All" thì đổi `_HARNESS` trong `chay_an_toan.py` để dừng ở ô lỗi đầu tiên.

## Phiếu trả lời Word (.docx)

Đội điền vào mẫu `Phieu_tra_loi_Vong_1_Olympic_AI_UNETI_2026.docx` của BTC và nộp kèm code.
Không truyền `--phieu` thì engine tự lấy file `.docx` trong thư mục bài nộp (`doc_phieu_word.py`,
chỉ dùng thư viện chuẩn).

- Bảng được nhận theo tiêu đề, không theo thứ tự; khoảng trắng thừa và chữ thường ở mảnh khóa được chấp nhận.
- Ô ghi sai định dạng (vd `14 (N)`, `9.`) không bị đoán: tính là sai và hiện cảnh báo `!` để người chấm xem lại.
- Ô để trống: tính là sai.

Cách nộp hiện tại: **5 file Python, mỗi bài 1 file** (gộp phần A/B/C), ví dụ
`bai_giai_mau/2_python_gop/` (`MAU_Bai1.py` … `MAU_Bai5.py` + `MAU_PhieuTraLoi_Vong1.docx`).

## Phiếu trả lời (JSON từ BE)

```json
{
  "ma_doi": "D01",
  "bai": {"1": {"A": 21, "B": 10, "C": 5, "K": 21, "manh_khoa": "U"}, "...": {}},
  "tu_khoa": "UNETI", "mat_khau": "UNETI70",
  "hidden": {"A": "UNETI 70", "B": "NAM VUON", "C": "XA"},
  "thong_diep": "UNETI – 70 NĂM VƯƠN XA"
}
```

## Thêm / sửa test ẩn

Sửa `de_bai.py`. Chỉ ghi dữ liệu mới, kết quả mong đợi tự tính từ hàm tham chiếu. Khi import,
file tự kiểm tra: đáp án khớp K chính thức và mỗi test ẩn cho kết quả **khác** đáp án đề.

## Chạy trên server

`chay_an_toan.py` mới cách ly ở mức tiến trình. Trên server nên chạy trong container:
không mạng, giới hạn RAM/CPU, user không quyền, ví dụ
`docker run --rm --network none --memory 256m --cpus 1 --read-only ...`.

`vi_du/` có các đội mẫu để thử:
- D01: mỗi phần một file, làm đúng (25/25).
- D02: các lỗi/gian lận điển hình (10/25).
- D03: gộp Bài 1 vào một file, Bài 2–5 vào một file tên tự do; cài lỗi ở 2A (`sorted`) và 3B (crash) (22/25).
- D04: notebook gộp A/B/C, file gộp A+B kèm C để file riêng (chỉ nộp Bài 2 và 4).
