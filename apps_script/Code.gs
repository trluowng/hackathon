/**
 * Olympic AI UNETI 2026 - Vòng 1.
 * Google Apps Script giữ: trang nộp bài (doGet + nopBai) + kho lưu bài trên Google Drive + API cho web chấm trên Vercel (doPost).
 *
 * Cài đặt (xem HUONG_DAN_DEPLOY.md):
 *   1. Dán Code.gs, Index.html vào project Apps Script.
 *   2. Chạy hàm caiDatLanDau() một lần -> tạo thư mục trên Drive, in ra khóa API.
 *   3. Deploy > New deployment > Web app: Execute as "Me", Who has access "Anyone".
 *
 * Lưu trữ:
 *   Drive:  OlympicAI_Vong1/bai_nop/<MÃ>/   mỗi đội MỘT thư mục: lần nộp thành công sau ĐÈ lên bài trước
 *           (file bài + kiem_tra.json, ket_qua.json, duyet.json của bài mới nhất). Lần nộp lỗi không đè.
 *   Google Sheet "Thong_ke_nop_bai_Vong1" (trong OlympicAI_Vong1): mỗi đội một dòng, cập nhật mỗi lần nộp và khi chấm.
 *   Script Properties: ln_<id> = thông tin từng lần nộp (để liệt kê nhanh), cd_<tên> = cài đặt, doi = danh sách đội.
 */
var TEN_THU_MUC_GOC = 'OlympicAI_Vong1';
var MUI_GIO = 'Asia/Ho_Chi_Minh';
var DUNG_LUONG_TOI_DA = 2 * 1024 * 1024;  // 2 MB mỗi file
var THONG_DIEP_DUNG = 'UNETI 70 NAM VUON XA';
var DUOI_CODE = ['.py', '.ipynb'];

function props_() {
  return PropertiesService.getScriptProperties();
}

/** Chạy MỘT LẦN trong trình soạn thảo: tạo thư mục lưu bài và khóa API cho Vercel. */
function caiDatLanDau() {
  var p = props_();
  if (!p.getProperty('ID_BAI_NOP')) {
    var goc = DriveApp.createFolder(TEN_THU_MUC_GOC);
    p.setProperty('ID_GOC', goc.getId());
    p.setProperty('ID_BAI_NOP', goc.createFolder('bai_nop').getId());
  }
  if (!p.getProperty('KHOA_API')) {
    p.setProperty('KHOA_API', Utilities.getUuid().replace(/-/g, '') + Utilities.getUuid().replace(/-/g, ''));
  }
  bangThongKe_();
  Logger.log('Thư mục lưu bài: https://drive.google.com/drive/folders/' + p.getProperty('ID_GOC'));
  Logger.log('File thống kê: https://docs.google.com/spreadsheets/d/' + p.getProperty('ID_SHEET'));
  Logger.log('APPS_SCRIPT_KHOA (dán vào Vercel): ' + p.getProperty('KHOA_API'));
}

// ---------- File thống kê (Google Sheet, tải về được dạng Excel) ----------

var COT_THONG_KE = ['Mã đội', 'Tên đội', 'Lần nộp gần nhất', 'Kết quả lần gần nhất', 'Lý do nộp lỗi',
  'Số lần nộp', 'Số lần nộp thành công', 'Bản được chấm (nộp lúc)', 'File đã nộp', 'Thư mục bài',
  'Trạng thái chấm', 'Tổng điểm', 'Bài 1', 'Bài 2', 'Bài 3', 'Bài 4', 'Bài 5'];
var TEN_TRANG_THAI = {cho_cham: 'Chờ chấm', dang_cham: 'Đang chấm', da_cham: 'Đã chấm', loi: 'Lỗi khi chấm',
  bo_qua: 'Bỏ qua'};

function bangThongKe_() {
  var p = props_();
  var id = p.getProperty('ID_SHEET');
  if (id) return SpreadsheetApp.openById(id).getSheets()[0];
  var ss = SpreadsheetApp.create('Thong_ke_nop_bai_Vong1');
  DriveApp.getFileById(ss.getId()).moveTo(DriveApp.getFolderById(p.getProperty('ID_GOC')));
  var sh = ss.getSheets()[0];
  sh.setName('Thống kê');
  sh.getRange('A:A').setNumberFormat('@');  // mã đội giữ nguyên dạng chữ (vd 001)
  sh.getRange(1, 1, 1, COT_THONG_KE.length).setValues([COT_THONG_KE]).setFontWeight('bold');
  sh.setFrozenRows(1);
  p.setProperty('ID_SHEET', ss.getId());
  return sh;
}

/** Sửa dòng của đội (thêm mới nếu chưa có). sua(hang) nhận {tên cột: giá trị} và sửa tại chỗ. Gọi trong khóa. */
function capNhatThongKe_(ma, sua) {
  var sh = bangThongKe_();
  var cuoi = sh.getLastRow();
  var cotMa = cuoi > 1 ? sh.getRange(2, 1, cuoi - 1, 1).getValues() : [];
  var dong = cuoi + 1;
  for (var i = 0; i < cotMa.length; i++) {
    if (String(cotMa[i][0]) === ma) { dong = i + 2; break; }
  }
  var giaTri = dong <= cuoi ? sh.getRange(dong, 1, 1, COT_THONG_KE.length).getValues()[0] : [];
  var hang = {};
  COT_THONG_KE.forEach(function (c, j) { hang[c] = giaTri[j] === undefined ? '' : giaTri[j]; });
  hang['Mã đội'] = ma;
  sua(hang);
  sh.getRange(dong, 1, 1, COT_THONG_KE.length).setValues([COT_THONG_KE.map(function (c) { return hang[c]; })]);
}

// ---------- Thời gian, trạng thái nộp ----------

function bayGio_() {
  return Utilities.formatDate(new Date(), MUI_GIO, "yyyy-MM-dd'T'HH:mm:ss");
}

/** Hạn nộp do admin đặt trên web chấm (lưu ở cd_han_nop, cd_mo_nop). */
function trangThaiNop_() {
  var p = props_();
  var han = p.getProperty('cd_han_nop') || '';
  if ((p.getProperty('cd_mo_nop') || '1') !== '1') return {duoc: false, ly_do: 'Ban Tổ chức đang khóa nộp bài.', han: han};
  if (han && bayGio_() > han) return {duoc: false, ly_do: 'Đã hết hạn nộp bài.', han: han};
  if (!p.getProperty('ID_BAI_NOP')) return {duoc: false, ly_do: 'Hệ thống chưa được cài đặt (chạy caiDatLanDau).', han: han};
  return {duoc: true, ly_do: '', han: han};
}

// ---------- Trang nộp bài ----------

function doGet() {
  var trang = HtmlService.createTemplateFromFile('Index');
  trang.trangThai = trangThaiNop_();
  return trang.evaluate()
    .setTitle('Nộp bài Vòng 1 · Olympic AI UNETI 2026')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

/**
 * Gọi từ trang nộp bài. p = {ma_doi, ten_doi, tep: [{o: 'phieu'|1..5, ten, b64}]}
 * Chỉ kiểm tra thông tin đội (mã, tên khớp phiếu) và loại file; đúng và đủ -> nộp thành công.
 * Lần nộp lỗi vẫn được lưu (đánh dấu lỗi) để admin xem, nhưng không chấm.
 */
function nopBai(p) {
  var tt = trangThaiNop_();
  if (!tt.duoc) return {ok: false, loi: [tt.ly_do]};
  var ma = String(p.ma_doi || '').trim().toUpperCase();
  var ten = String(p.ten_doi || '').trim().slice(0, 100);
  if (!/^[A-Za-z0-9_\-]{1,30}$/.test(ma)) return {ok: false, loi: ["Mã đội chỉ gồm chữ không dấu, số, '-' hoặc '_' (tối đa 30 ký tự)."]};
  if (!ten) return {ok: false, loi: ['Chưa nhập tên đội (phải giống tên đội ghi trong phiếu trả lời).']};

  var tep = (p.tep || []).map(function (t) {
    return {o: t.o, ten: String(t.ten || ''), bytes: Utilities.base64Decode(t.b64 || '')};
  });
  var loi = loiTep_(tep);
  var hidden = false;
  if (!loi.length) {
    var phieu = null;
    try {
      var xml = xmlPhieu_(tep.filter(function (t) { return t.o === 'phieu'; })[0].bytes);
      phieu = xml ? docPhieu_(xml) : null;
    } catch (e) {
      phieu = null;
    }
    if (!phieu || !phieu.co_bang_ket_qua) {
      loi.push('Phiếu trả lời không đọc được hoặc không đúng mẫu của Ban Tổ chức.');
    } else {
      loi = loi.concat(doiChieuPhieu_(phieu, ma, ten));
      hidden = chuanNhan_(phieu.thong_diep) === THONG_DIEP_DUNG;
    }
  }
  var luc = bayGio_();
  luuLanNop_(ma, ten, luc, tep, loi.length ? loi : null, hidden && !loi.length);
  if (loi.length) return {ok: false, loi: loi};
  return {ok: true, ma_doi: ma, ten_doi: ten, thoi_gian: luc};
}

function duoi_(ten) {
  var m = String(ten).toLowerCase().match(/\.[a-z0-9]{1,8}$/);
  return m ? m[0] : '';
}

/** Lỗi về file của từng ô nộp. tep: [{o, ten, bytes hoặc kich_thuoc}] */
function loiTep_(tep) {
  var loi = [];
  tep.forEach(function (t) {
    var tenO = t.o === 'phieu' ? 'Phiếu trả lời' : 'Bài ' + t.o;
    var choPhep = t.o === 'phieu' ? ['.docx'] : DUOI_CODE;
    var kichThuoc = t.bytes ? t.bytes.length : t.kich_thuoc;
    if (choPhep.indexOf(duoi_(t.ten)) < 0) {
      loi.push('Ô ' + tenO + ' chỉ nhận file ' + choPhep.join(' hoặc ') + ' (đã chọn: ' + t.ten + ').');
    } else if (kichThuoc > DUNG_LUONG_TOI_DA) {
      loi.push('Ô ' + tenO + ': file ' + t.ten + ' quá 2 MB.');
    } else if (!kichThuoc) {
      loi.push('Ô ' + tenO + ': file ' + t.ten + ' rỗng.');
    } else if (t.o === 'phieu' && t.bytes && !(t.bytes[0] === 80 && t.bytes[1] === 75)) {  // file .docx bắt đầu bằng "PK"
      loi.push('Ô ' + tenO + ': ' + t.ten + ' không phải file Word .docx hợp lệ.');
    }
  });
  if (!tep.some(function (t) { return t.o === 'phieu'; })) loi.unshift('Chưa chọn phiếu trả lời (file Word .docx).');
  if (!tep.some(function (t) { return t.o !== 'phieu'; })) loi.push('Chưa chọn file bài làm nào.');
  return loi;
}

function thuMucDoi_(ma) {
  var baiNop = DriveApp.getFolderById(props_().getProperty('ID_BAI_NOP'));
  var it = baiNop.getFoldersByName(ma);
  return it.hasNext() ? it.next() : baiNop.createFolder(ma);
}

/**
 * Lần nộp thành công: ĐÈ bài cũ của đội (bỏ hết file cũ, kể cả kết quả chấm cũ) -> thư mục đội chỉ còn bài mới nhất.
 * Lần nộp lỗi: không đụng tới bài đang có, chỉ ghi lại để admin và file thống kê biết.
 */
function luuLanNop_(ma, ten, luc, tep, loi, hidden) {
  var p = props_();
  var gon = luc.replace(/[-:]/g, '').replace('T', '-');
  var id = gon + '-' + ma + '-' + Utilities.getUuid().slice(0, 6);
  // ms: thứ tự nộp chính xác tới mili giây (hai lần nộp trong cùng một giây vẫn phân biệt được)
  var ghi = {id: id, ma_doi: ma, ten_doi: ten, thoi_gian: luc, ms: new Date().getTime(), loi: loi, hidden: hidden,
             thu_muc: '', cac_file: []};
  if (!loi) {
    var thuMuc = thuMucDoi_(ma);
    var cu = thuMuc.getFiles();
    while (cu.hasNext()) cu.next().setTrashed(true);
    tep.forEach(function (t) {
      var tenFile = ma + '_' + (t.o === 'phieu' ? 'PhieuTraLoi' : 'Bai' + t.o) + duoi_(t.ten);
      thuMuc.createFile(Utilities.newBlob(t.bytes, 'application/octet-stream', tenFile));
      ghi.cac_file.push(tenFile);
    });
    ghi.thu_muc = thuMuc.getId();
  }
  var khoa = LockService.getScriptLock();
  khoa.waitLock(120000);
  try {
    if (!loi) {  // các lần nộp trước của đội không còn file (đã bị bản mới đè)
      API_.ds().forEach(function (r) {
        if (r.ma_doi === ma && r.id !== id && !r.thay_the && !r.loi) {
          r.thay_the = true;
          r.cac_file = [];
          p.setProperty('ln_' + r.id, JSON.stringify(r));
        }
      });
    }
    p.setProperty('ln_' + id, JSON.stringify(ghi));
    capNhatThongKe_(ma, function (h) {
      if (!loi || !h['Tên đội']) h['Tên đội'] = ten;
      h['Lần nộp gần nhất'] = luc;
      h['Kết quả lần gần nhất'] = loi ? 'Nộp lỗi' : 'Nộp thành công';
      h['Lý do nộp lỗi'] = loi ? loi.join(' | ') : '';
      h['Số lần nộp'] = (Number(h['Số lần nộp']) || 0) + 1;
      if (!loi) {
        h['Số lần nộp thành công'] = (Number(h['Số lần nộp thành công']) || 0) + 1;
        h['Bản được chấm (nộp lúc)'] = luc;
        h['File đã nộp'] = ghi.cac_file.join(', ');
        h['Thư mục bài'] = 'https://drive.google.com/drive/folders/' + ghi.thu_muc;
        h['Trạng thái chấm'] = 'Chưa chấm';
        ['Tổng điểm', 'Bài 1', 'Bài 2', 'Bài 3', 'Bài 4', 'Bài 5'].forEach(function (c) { h[c] = ''; });
      }
    });
  } finally {
    khoa.releaseLock();
  }
}

/** Lần nộp thành công mới nhất của đội (bản được chấm). */
function banChamCuaDoi_(ma) {
  var ds = API_.ds().filter(function (r) { return r.ma_doi === ma && !r.loi && !r.thay_the; });
  ds.sort(function (a, b) { return (a.ms || 0) - (b.ms || 0); });
  return ds.length ? ds[ds.length - 1] : null;
}

// ---------- Đọc phiếu Word (thuần JavaScript, không phụ thuộc Apps Script - test được bằng Node) ----------

function xmlPhieu_(bytes) {
  var cacFile = Utilities.unzip(Utilities.newBlob(bytes, 'application/zip', 'phieu.zip'));
  for (var i = 0; i < cacFile.length; i++) {
    if (cacFile[i].getName() === 'word/document.xml') return cacFile[i].getDataAsString('UTF-8');
  }
  return null;
}

function boDau_(s) {
  return String(s || '').replace(/đ/g, 'd').replace(/Đ/g, 'D').normalize('NFD').replace(/[̀-ͯ]/g, '');
}

/** 'Kết quả giải mã – Thành viên A' -> 'KET QUA GIAI MA THANH VIEN A' (để so nhãn). */
function chuanNhan_(s) {
  return boDau_(s).toUpperCase().replace(/[^A-Z0-9]+/g, ' ').trim();
}

/** So tên không phân biệt hoa/thường, khoảng trắng thừa, kiểu mã hóa dấu (NFC/NFD). */
function chuanTen_(s) {
  return String(s || '').normalize('NFC').toLowerCase().split(/\s+/).filter(Boolean).join(' ');
}

function giaiMaXml_(s) {
  return s.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&apos;/g, "'")
    .replace(/&#(\d+);/g, function (_, n) { return String.fromCharCode(+n); }).replace(/&amp;/g, '&');
}

/** Chữ trong một đoạn XML (ô bảng / đoạn văn); các đoạn văn nối bằng khoảng trắng. */
function chu_(xml) {
  var ra = [];
  var re = /<w:t(?:\s[^>]*)?>([^<]*)<\/w:t>|<w:(?:tab|br)\/>|<\/w:p>/g;
  var m;
  while ((m = re.exec(xml))) ra.push(m[1] !== undefined ? giaiMaXml_(m[1]) : ' ');
  return ra.join('').replace(/\s+/g, ' ').trim();
}

/** Lấy mã đội, tên đội, thông điệp cuối và kiểm tra có bảng kết quả 5 bài (đúng mẫu BTC). */
function docPhieu_(xml) {
  var kq = {ma_doi: '', ten_doi: '', thong_diep: '', co_bang_ket_qua: false};
  var than = (xml.match(/<w:body>([\s\S]*)<\/w:body>/) || [null, ''])[1];
  var re = /<w:tbl[ >][\s\S]*?<\/w:tbl>|<w:p[ >][\s\S]*?<\/w:p>/g;
  var doanTruoc = '';
  var m;
  while ((m = re.exec(than))) {
    var khoi = m[0];
    if (khoi.indexOf('<w:tbl') !== 0) {
      var t = chu_(khoi);
      if (t) doanTruoc = chuanNhan_(t);
      continue;
    }
    var hang = (khoi.match(/<w:tr[ >][\s\S]*?<\/w:tr>/g) || []).map(function (tr) {
      return (tr.match(/<w:tc[ >][\s\S]*?<\/w:tc>/g) || []).map(chu_);
    });
    if (!hang.length) continue;
    var tieuDe = hang[0].map(chuanNhan_);
    var co = function (chuoi) { return tieuDe.some(function (c) { return c.indexOf(chuoi) >= 0; }); };
    if (co('KET QUA A') && co('CHECKPOINT')) {
      kq.co_bang_ket_qua = true;
    } else if (hang.length === 1 && hang[0].length === 1 && doanTruoc.indexOf('THONG DIEP CUOI CUNG') >= 0) {
      kq.thong_diep = hang[0][0];
    } else {
      hang.forEach(function (h) {
        if (h.length >= 2 && chuanNhan_(h[0]).indexOf('MA DOI') === 0) {
          kq.ma_doi = h[1];
          if (h.length >= 4 && chuanNhan_(h[2]).indexOf('TEN DOI') === 0) kq.ten_doi = h[3];
        }
      });
    }
  }
  return kq;
}

/** Mã đội và tên đội nhập khi nộp phải khớp phiếu trả lời; trả về danh sách lỗi. */
function doiChieuPhieu_(phieu, ma, ten) {
  var loi = [];
  if (!phieu.ma_doi) loi.push('Phiếu trả lời chưa ghi Mã đội.');
  else if (phieu.ma_doi.replace(/\s/g, '').toUpperCase() !== ma) {
    loi.push('Mã đội trong phiếu trả lời (' + phieu.ma_doi + ') khác mã đội đã nhập (' + ma + ').');
  }
  if (!phieu.ten_doi) loi.push('Phiếu trả lời chưa ghi Tên đội.');
  else if (chuanTen_(phieu.ten_doi) !== chuanTen_(ten)) {
    loi.push('Tên đội trong phiếu trả lời (' + phieu.ten_doi + ') khác tên đội đã nhập (' + ten + ').');
  }
  return loi;
}

// ---------- API cho web chấm (Vercel) ----------

function doPost(e) {
  var kq;
  try {
    var yc = JSON.parse(e.postData.contents);
    var khoa = props_().getProperty('KHOA_API');
    if (!khoa || yc.khoa !== khoa) throw new Error('Sai khóa API');
    var ham = API_[yc.hanh_dong];
    if (!ham) throw new Error('Không có hành động: ' + yc.hanh_dong);
    kq = {ok: true, du_lieu: ham(yc)};
  } catch (err) {
    kq = {ok: false, loi: String((err && err.message) || err)};
  }
  return ContentService.createTextOutput(JSON.stringify(kq)).setMimeType(ContentService.MimeType.JSON);
}

function banGhi_(id) {
  var s = props_().getProperty('ln_' + id);
  if (!s) throw new Error('Không có lần nộp ' + id);
  return JSON.parse(s);
}

function timFile_(thuMuc, ten) {
  var it = thuMuc.getFilesByName(ten);
  return it.hasNext() ? it.next() : null;
}

var API_ = {
  /** Mọi lần nộp (thông tin ngắn, đọc từ Script Properties - một lần gọi). */
  ds: function () {
    var tatCa = props_().getProperties();
    return Object.keys(tatCa).filter(function (k) { return k.indexOf('ln_') === 0; })
      .map(function (k) { return JSON.parse(tatCa[k]); });
  },
  /** Cài đặt (hạn nộp, mở/khóa nộp, khóa phiên...). */
  cai_dat: function () {
    var tatCa = props_().getProperties();
    var ra = {};
    Object.keys(tatCa).forEach(function (k) { if (k.indexOf('cd_') === 0) ra[k.slice(3)] = tatCa[k]; });
    return ra;
  },
  ghi_cai_dat: function (yc) {
    props_().setProperty('cd_' + yc.ten, String(yc.gia_tri));
    return true;
  },
  doi: function () {
    return JSON.parse(props_().getProperty('doi') || '{}');
  },
  /** Link thư mục bài nộp và file thống kê để trang admin hiển thị. */
  lien_ket: function () {
    bangThongKe_();
    var p = props_();
    return {thu_muc: 'https://drive.google.com/drive/folders/' + p.getProperty('ID_GOC'),
            thong_ke: 'https://docs.google.com/spreadsheets/d/' + p.getProperty('ID_SHEET')};
  },
  ghi_doi: function (yc) {
    props_().setProperty('doi', JSON.stringify(yc.du_lieu || {}));
    return true;
  },
  /** File bài nộp (base64). yc.ten: chỉ lấy một file. Lần nộp đã bị đè / nộp lỗi: không có file. */
  tai_file: function (yc) {
    var ghi = banGhi_(yc.id);
    var ra = {};
    if (!ghi.thu_muc || ghi.thay_the) return ra;
    var thuMuc = DriveApp.getFolderById(ghi.thu_muc);
    ghi.cac_file.forEach(function (ten) {
      if (yc.ten && ten !== yc.ten) return;
      var f = timFile_(thuMuc, ten);
      if (f) ra[ten] = Utilities.base64Encode(f.getBlob().getBytes());
    });
    return ra;
  },
  /** Đọc / ghi file JSON trong thư mục lần nộp: kiem_tra.json, ket_qua.json, duyet.json. */
  doc_json: function (yc) {
    var ghi = banGhi_(yc.id);
    if (!ghi.thu_muc || ghi.thay_the) return null;  // file trong thư mục đội giờ thuộc về bài mới hơn
    var f = timFile_(DriveApp.getFolderById(ghi.thu_muc), yc.ten);
    return f ? JSON.parse(f.getBlob().getDataAsString('UTF-8')) : null;
  },
  ghi_json: function (yc) {
    if (['kiem_tra.json', 'ket_qua.json', 'duyet.json'].indexOf(yc.ten) < 0) throw new Error('Tên file không hợp lệ');
    var ghi = banGhi_(yc.id);
    if (!ghi.thu_muc || ghi.thay_the) throw new Error('Lần nộp này không còn là bài mới nhất của đội');
    var thuMuc = DriveApp.getFolderById(ghi.thu_muc);
    var noiDung = JSON.stringify(yc.du_lieu);
    var f = timFile_(thuMuc, yc.ten);
    if (f) f.setContent(noiDung);
    else thuMuc.createFile(yc.ten, noiDung, 'application/json');
    return true;
  },
  /** Sửa thông tin ngắn của lần nộp (trạng thái chấm, điểm tóm tắt). */
  sua_ban_ghi: function (yc) {
    var khoa = LockService.getScriptLock();
    khoa.waitLock(20000);
    try {
      var ghi = banGhi_(yc.id);
      Object.keys(yc.sua || {}).forEach(function (k) {
        if (['id', 'ma_doi', 'thoi_gian', 'thu_muc', 'cac_file', 'loi', 'hidden', 'thay_the'].indexOf(k) < 0) {
          ghi[k] = yc.sua[k];
        }
      });
      props_().setProperty('ln_' + yc.id, JSON.stringify(ghi));
      var banCham = banChamCuaDoi_(ghi.ma_doi);
      if (banCham && banCham.id === ghi.id) {  // ghi trạng thái chấm + điểm của bài mới nhất vào file thống kê
        capNhatThongKe_(ghi.ma_doi, function (h) {
          h['Trạng thái chấm'] = TEN_TRANG_THAI[ghi.tt] || ghi.tt || '';
          var coDiem = ghi.tt === 'da_cham' && ghi.tong !== undefined && ghi.tong !== null;
          h['Tổng điểm'] = coDiem ? ghi.tong : '';
          for (var i = 1; i <= 5; i++) h['Bài ' + i] = coDiem && ghi.diem_bai ? ghi.diem_bai[i - 1] : '';
        });
      }
      return true;
    } finally {
      khoa.releaseLock();
    }
  }
};
