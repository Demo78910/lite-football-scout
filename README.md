# LITE FOOTBALL SCOUT — PWA 2.1

## วิธีใช้งาน
1. เลือกหัวข้อวิเคราะห์และวันที่ในแท็บค้นหา
2. กดสร้างคำสั่ง แล้วคัดลอกไปวางใน ChatGPT
3. ให้ ChatGPT ค้นหาคู่ที่ยังไม่เริ่มแข่ง พร้อมอ้างอิงแหล่งข้อมูล
4. นำผลกลับมาวางในช่องนำเข้าผลจาก ChatGPT
5. เลือกคู่จากแท็บคู่แนะนำ แล้วกรอกราคาจริงทีละคู่
6. คัดลอกข้อมูลทั้งหมดกลับไปให้ ChatGPT วิเคราะห์ความคุ้มค่า

## ติดตั้ง PWA ผ่าน GitHub Pages
1. Repository Settings > Pages
2. Build and deployment: Deploy from a branch
3. Branch: main, Folder: /(root), Save
4. รอ GitHub สร้าง URL https://OWNER.github.io/lite-football-scout/
5. เปิด URL ใน Safari บน iPhone > Share > Add to Home Screen > Add

## ข้อจำกัด
- เว็บนี้ไม่มี API จึงไม่ดึงตารางแข่ง ข่าว หรือราคาบอลเอง
- ChatGPT ทำหน้าที่ค้นคว้าภายนอก โดยผู้ใช้คัดลอกผลเข้าเว็บ
- ราคาต้องกรอกเองจากแหล่งจริง
- ข้อมูลบันทึกใน localStorage ของเบราว์เซอร์เครื่องนี้ ควร Export JSON สำรอง
- ไม่มีการรับประกันผลหรือกำไร
