"""Cấp quyền Google Drive cho web - chạy MỘT LẦN trên máy bạn.

Cách dùng:
    python lay_token_drive.py <GOOGLE_CLIENT_ID> <GOOGLE_CLIENT_SECRET>

Script mở trình duyệt để bạn đăng nhập Google và đồng ý, rồi:
  - tạo thư mục "OlympicAI_Vong1" trong Drive của bạn (nơi lưu bài nộp),
  - in ra GOOGLE_REFRESH_TOKEN và DRIVE_FOLDER_ID để dán vào Environment Variables trên Vercel.
Quyền xin là drive.file: web chỉ thấy/sửa file do chính nó tạo, không đọc được file khác trong Drive.
Chỉ dùng thư viện chuẩn của Python.
"""
import base64
import hashlib
import http.server
import json
import secrets
import sys
import urllib.parse
import urllib.request
import webbrowser

PHAM_VI = "https://www.googleapis.com/auth/drive.file"


def _post(url, du_lieu):
    with urllib.request.urlopen(url, urllib.parse.urlencode(du_lieu).encode()) as r:
        return json.load(r)


def _tao_thu_muc(token, ten, cha, nhan):
    meta = {"name": ten, "mimeType": "application/vnd.google-apps.folder", "appProperties": nhan}
    if cha:
        meta["parents"] = [cha]
    yeu_cau = urllib.request.Request("https://www.googleapis.com/drive/v3/files?fields=id",
                                     data=json.dumps(meta).encode(), method="POST",
                                     headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
    with urllib.request.urlopen(yeu_cau) as r:
        return json.load(r)["id"]


def _tao_json(token, ten, cha, nhan):
    ranh_gioi = secrets.token_hex(16)
    meta = {"name": ten, "parents": [cha], "appProperties": nhan}
    than = ("--%s\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n%s\r\n--%s\r\n"
            "Content-Type: application/json\r\n\r\n{}\r\n--%s--" % (ranh_gioi, json.dumps(meta), ranh_gioi, ranh_gioi))
    yeu_cau = urllib.request.Request(
        "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id", data=than.encode(),
        method="POST", headers={"Authorization": "Bearer " + token,
                                "Content-Type": "multipart/related; boundary=%s" % ranh_gioi})
    with urllib.request.urlopen(yeu_cau) as r:
        return json.load(r)["id"]


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    client_id, client_secret = sys.argv[1], sys.argv[2]
    ma_xac_minh = secrets.token_urlsafe(64)
    thach_thuc = base64.urlsafe_b64encode(hashlib.sha256(ma_xac_minh.encode()).digest()).rstrip(b"=").decode()
    trang_thai = secrets.token_urlsafe(16)
    nhan_duoc = {}

    class NhanMa(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            nhan_duoc.update({k: v[0] for k, v in q.items()})
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write("<h2>Đã nhận quyền. Quay lại cửa sổ dòng lệnh.</h2>".encode())

        def log_message(self, *a):
            pass

    may_chu = http.server.HTTPServer(("127.0.0.1", 0), NhanMa)
    chuyen_ve = "http://127.0.0.1:%d" % may_chu.server_port
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
        "client_id": client_id, "redirect_uri": chuyen_ve, "response_type": "code", "scope": PHAM_VI,
        "access_type": "offline", "prompt": "consent", "state": trang_thai,
        "code_challenge": thach_thuc, "code_challenge_method": "S256"})
    print("Đang mở trình duyệt để đăng nhập Google. Nếu không tự mở, chép link này vào trình duyệt:\n\n%s\n" % url)
    webbrowser.open(url)
    while "code" not in nhan_duoc and "error" not in nhan_duoc:
        may_chu.handle_request()
    if nhan_duoc.get("state") != trang_thai or "code" not in nhan_duoc:
        sys.exit("Không nhận được quyền: %s" % nhan_duoc)

    token = _post("https://oauth2.googleapis.com/token", {
        "code": nhan_duoc["code"], "client_id": client_id, "client_secret": client_secret,
        "redirect_uri": chuyen_ve, "grant_type": "authorization_code", "code_verifier": ma_xac_minh})
    if "refresh_token" not in token:
        sys.exit("Google không trả về refresh token: %s" % token)

    # Tạo sẵn cả cấu trúc để web không phải tự tạo (tránh tạo trùng khi nhiều request đến cùng lúc)
    at = token["access_token"]
    goc = _tao_thu_muc(at, "OlympicAI_Vong1", None, {"olympic": "goc"})
    _tao_thu_muc(at, "bai_nop", goc, {"olympic": "bai_nop"})
    _tao_json(at, "cai_dat.json", goc, {"olympic": "cai_dat"})
    _tao_json(at, "doi.json", goc, {"olympic": "doi"})
    print("Đã tạo thư mục OlympicAI_Vong1 (bai_nop, cai_dat.json, doi.json) trong Google Drive của bạn.\n")
    print("Dán các giá trị sau vào Vercel > Settings > Environment Variables:\n")
    print("GOOGLE_CLIENT_ID     = %s" % client_id)
    print("GOOGLE_CLIENT_SECRET = %s" % client_secret)
    print("GOOGLE_REFRESH_TOKEN = %s" % token["refresh_token"])
    print("DRIVE_FOLDER_ID      = %s" % goc)
    print("\nGiữ bí mật các giá trị này, KHÔNG đưa lên Git.")


if __name__ == "__main__":
    main()
