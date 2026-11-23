# VOICE STUDIO — Hướng dẫn dùng (đọc 2 phút là chạy được)

Tool này chỉ làm 1 việc: biến **script chữ thành giọng đọc** cho video.
Quy trình: **dán script (mỗi dòng 1 câu) → chọn giọng → bấm TẠO GIỌNG → nhận file `voice.mp3` + `timings.json`** (bảng mốc thời gian từng câu, để cắt hình khớp theo giọng).

**Tổng 20 giọng, 4 nhóm:**

- **VIỆT — EDGE (cần mạng):** Nam Minh, Hoài My — giọng của Microsoft chạy qua Internet.
- **ANH — EDGE (cần mạng):** Guy, Andrew, Brian, Eric, Christopher, Jenny.
- **ANH — KOKORO (chạy ngay trên máy, không cần mạng):** đủ 11 giọng (am_adam, am_michael, bm_george, bm_lewis, af_bella, af_sarah, af_nicole, af_sky, af, bf_emma, bf_isabella). Model Kokoro đi kèm sẵn trong gói.
- **MÁY BẠN — SAPI:** giọng có sẵn trong Windows (David / Zira).

**Không cần API key, không cần tài khoản, không tốn phí.**

---

## 1. Chạy tool lần đầu

1. Giải nén cả gói Voice Studio vào 1 thư mục trên máy (để ở Desktop là dễ tìm nhất). **Đừng tách lẻ file** — các thư mục `models`, `fonts` phải nằm cạnh file `run.bat`.
2. Nháy đúp vào **`run.bat`**.
   - Sẽ có 1 cửa sổ đen hiện lên: nó tự tìm Python, tự cài các gói còn thiếu (**lần đầu cần mạng Internet, chờ vài phút**), xong cửa sổ tool tự mở.
   - Các lần sau mở nhanh hơn vì không phải cài lại.
3. Cửa sổ tool mở ra: nền đen, chữ pixel.

> Nếu cửa sổ đen báo `[LOI] Chua thay Python`: máy chưa có Python. Cài **Python 3.10–3.12** từ **python.org** — ở màn hình cài đặt đầu tiên nhớ tick ô **"Add python.exe to PATH"** (ô này ở dưới cùng cửa sổ cài), rồi chạy lại `run.bat`. (Bản Python mới hơn 3.12 có thể chưa có sẵn gói Kokoro tương thích.)

> Nếu tool báo **thiếu ffmpeg**: ffmpeg là phần mềm xử lý âm thanh mà tool cần để xuất file mp3 và đọc giọng Edge. Cài bằng cách mở PowerShell (gõ "powershell" ở menu Start) rồi gõ lệnh: `winget install Gyan.FFmpeg` — chờ cài xong, tắt tool mở lại là được.

## 2. Tạo giọng — 5 bước đúng thứ tự trên cửa sổ

1. **DÁN SCRIPT** — chuẩn bị script dạng mỗi dòng là 1 câu. Bôi đen copy cả đoạn, bấm nút **DÁN SCRIPT MỚI** trong tool (hoặc bấm vào ô chữ rồi Ctrl+V). Dưới ô có dòng đếm số câu để đối chiếu.
   - Muốn 1 chỗ nào đó được đọc **nhấn mạnh hơn**: bọc chỗ đó bằng dấu sao, ví dụ: `Nó rẻ hơn tới *20 phần trăm*.` — và nhớ để ô tick "Tự nhấn chữ *bọc sao*" đang bật.
2. **CHỌN GIỌNG** — bấm chọn 1 giọng ở khung TẦNG 1. Bấm **▶ NGHE 5s** để nghe thử giọng đó đọc 1 câu mẫu trước khi quyết.
   - Các giọng **Edge cần mạng Internet** khi tạo (đọc bằng máy chủ của Microsoft). Giọng **Kokoro chạy ngay trên máy, không cần mạng**.
   - **SAPI — David / Zira** là giọng có sẵn trong Windows của bạn.
3. **CHỈNH TÔNG** — khung TẦNG 2:
   - **TỐC ĐỘ**: mặc định 1.25x. Thường để 1.0–1.25x tùy ý.
   - **CAO ĐỘ**: giọng trầm hơn / cao hơn. Để 1.00x là giọng gốc.
   - **NGHỈ GIỮA CÂU**: khoảng lặng chèn giữa 2 câu, mặc định 0.35 giây.
4. **TẠO GIỌNG** — bấm nút xanh lá to. Tool đọc **từng câu riêng** (dòng trạng thái dưới nút sẽ báo "Đang đọc câu 3/16..."), chờ tới khi báo xong. Script dài thì chờ lâu hơn — đừng tắt giữa chừng. Cần dừng thì bấm **HỦY / LÀM LẠI**.
5. **LẤY FILE KẾT QUẢ** — xem mục 3 dưới đây.

## 3. File kết quả ở đâu

Sau khi tạo xong, ở thư mục của tool có thư mục **`output`** chứa:

- **`voice.mp3`** — bản giọng hoàn chỉnh (kèm `voice.wav` là bản gốc chất lượng cao hơn).
- **`timings.json`** — bảng mốc thời gian: câu số mấy bắt đầu ở giây nào, kết thúc ở giây nào. Dùng file này để cắt hình khớp theo giọng, giọng không bị tràn sang shot sau.
- **`log.txt`** — nhật ký chạy của tool; gặp lỗi thì xem file này để biết nguyên nhân.

Trong tool cũng có nút **NGHE LẠI** để nghe kiểm tra bản giọng, và nút **MỞ THƯ MỤC OUTPUT** để mở nhanh thư mục kết quả.

## 4. Gặp lỗi thì sao

- Tool báo lỗi bằng hộp thoại tiếng Việt — đọc theo nội dung hộp thoại trước.
- Giọng Edge báo lỗi sau 3 lần thử: thường do mạng chập chờn hoặc Microsoft bóp kết nối tạm thời. Kiểm tra mạng rồi bấm TẠO GIỌNG lại, hoặc đổi sang giọng Kokoro (chạy trên máy, không cần mạng).
- Vẫn không xử lý được: mở file `output/log.txt`, xem dòng lỗi cuối cùng — đa số trường hợp là thiếu ffmpeg hoặc thiếu gói Python (chạy lại `run.bat` để tool tự cài lại).
