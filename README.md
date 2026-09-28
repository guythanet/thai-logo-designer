# thai-logo-designer 🇹🇭

สกิลให้ Claude ออกแบบโลโก้เป็น SVG — สัมภาษณ์ → ร่างหลายแบบ → ปรับทีละรอบ → ส่งออก PNG + favicon
จุดเด่น: **ตัวอักษรไทยถูกต้อง** สระ/วรรณยุกต์ไม่ลอย ไม่ชน ไม่กลายเป็นกล่อง

A Claude skill for designing logos as SVG, with correct Thai lettering.

## ทำอะไรได้
- แปลงข้อความไทย/อังกฤษเป็นรูปทรง (HarfBuzz shaping) → เปิดที่ไหนก็หน้าตาเหมือนเดิม
- ฟอนต์ไทยในตัว: Kanit, Prompt, IBM Plex Sans Thai (ใช้เชิงพาณิชย์ได้)
- ตรวจอัตโนมัติ: ตัวไทยที่ยังไม่แปลง, ภาพล้นขอบ, เส้นบางเกินจนย่อแล้วหาย
- หน้า preview เทียบหลายแบบ + เช็กขนาด 64/32/16px + สลับพื้นหลัง
- ส่งออก PNG 16–2048px ตามสัดส่วนจริง + favicon.ico

## ติดตั้ง

### Claude Code
```
/plugin marketplace add guythanet/thai-logo-designer
/plugin install thai-logo-designer@thai-logo-designer
```

### claude.ai / Claude Desktop
1. ดาวน์โหลด `thai-logo-designer.skill` จากหน้า [Releases](../../releases)
2. Customize → Skills → + → Upload a skill
3. เปิด Code execution ใน Settings → Capabilities ไว้ด้วย

### ติดตั้งเครื่องมือเสริม (ครั้งเดียว)
```
pip install uharfbuzz fonttools cairosvg pillow
```

## ลองใช้
> ทำโลโก้ร้านกาแฟชื่อ "ดอยช้าง" ให้หน่อย โทนน้ำตาลอบอุ่น

## เครดิต
- แนวคิด workflow ได้แรงบันดาลใจจาก [neonwatty/logo-designer-skill](https://github.com/neonwatty/logo-designer-skill) (MIT)
- ฟอนต์: Kanit, Prompt (Cadson Demak), IBM Plex Sans Thai (IBM) — SIL Open Font License, ดู `skills/thai-logo-designer/assets/fonts/`

## License
MIT (code) · OFL (fonts)
