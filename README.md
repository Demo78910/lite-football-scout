# LITE FOOTBALL SCOUT — PWA 2.2

## เชื่อม API-Football โดยตรง
1. สมัครบัญชีฟรีที่ https://dashboard.api-football.com/register
2. สร้าง/คัดลอก API Key จาก Dashboard
3. เปิดเว็บแอป ไปที่แท็บค้นหา แล้ววาง API Key ในช่องเชื่อม API-Football
4. กดบันทึก API Key แล้วเลือกวันที่แข่งขัน
5. กดดึงโปรแกรมแข่งจาก API ตามวันที่เลือก
6. เลือกคู่ที่ต้องการแล้วกดเพิ่มเข้าคู่แนะนำ

## โควตาและข้อควรระวัง
- แพ็กเกจฟรีปัจจุบันระบุ 100 requests ต่อวัน
- แอปเรียก Fixtures endpoint หนึ่งครั้งต่อวันที่ค้นหา และเก็บแคช 30 นาทีในเครื่อง
- API Key ถูกเก็บใน localStorage ของเบราว์เซอร์ ไม่ได้ถูกเขียนลง GitHub แต่ผู้ที่เข้าถึงเบราว์เซอร์/เครื่องนี้อาจเห็นคีย์ได้
- ห้ามส่ง API Key ในแชตสาธารณะหรือ commit ลง repository
- หน้าเว็บเป็น static app จึงเรียก API จาก iPhone โดยตรงตามการรองรับ CORS ของ API-Football
- เวอร์ชันนี้เชื่อมโปรแกรมแข่งขันโดยตรงก่อน ส่วนสถิติย้อนหลัง, การบาดเจ็บ, standings และ odds จะเพิ่มเป็นการเรียกแบบเลือกคู่เพื่อประหยัดโควตา
- ราคาอาจไม่มีให้ครบทุกลีก/ทุกคู่ และข้อมูล pre-match odds ไม่ใช่ราคาสดตลอดเวลา
- สถานะ NS = ยังไม่เริ่ม, TBD = เวลาแข่งขันยังไม่กำหนด

## การติดตั้ง PWA
1. เปิด https://demo78910.github.io/lite-football-scout/ ด้วย Safari
2. Share > Add to Home Screen > Add

## สำรองข้อมูล
ใช้แท็บประวัติ > ส่งออกข้อมูลสำรอง JSON


## Automated data refresh (free setup)
The repository includes a GitHub Actions workflow that refreshes today's and tomorrow's fixtures and available pre-match odds every 6 hours. It uses the API-Football free quota conservatively (up to 4 dates/endpoint calls per run; normally 16 calls/day).

### One-time setup on iPhone
1. Open the repository: https://github.com/Demo78910/lite-football-scout
2. Settings > Secrets and variables > Actions > New repository secret.
3. Name: `API_FOOTBALL_KEY`
4. Value: paste the replacement API-Football key. Do not paste it into chat or commit it to files.
5. Save. Open Actions > Update football data > Run workflow for the first refresh.

The public snapshot will be written to `data/football.json`. Do not put the API key in this JSON or in the frontend.

### Important limits
- API-Football Free currently lists 100 requests/day; the workflow uses at most 4 calls per run and runs every 6 hours (typically up to 16 calls/day).
- Pre-match odds are not guaranteed for every fixture or league. API-Football documents odds refreshes about every 3 hours and coverage varying by competition/bookmaker.
- Thscore99 is a secondary manual verification source; this workflow does not scrape it. Automated scraping may be blocked or prohibited by the site.
- GPT analysis is not invoked automatically: free GitHub Actions can collect and publish data, but calling a paid GPT API is not part of a $0 setup. Use the app's copy-for-ChatGPT action to pass the latest snapshot into ChatGPT.
