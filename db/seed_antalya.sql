-- ============================================================
-- SafeRoad — Antalya Mock Data Seed (FIXED)
-- 25 incidents across 5 districts, using REAL user/category/municipality IDs
-- Run:
--   cd Backend-FastAPI && source .venv/bin/activate
--   python3 -c "
--   import asyncio, asyncpg, pathlib, os
--   from dotenv import load_dotenv; load_dotenv()
--   async def run():
--       conn = await asyncpg.connect(os.getenv('SUPABASE_DB_URL'), ssl='require')
--       await conn.execute(pathlib.Path('db/seed_antalya.sql').read_text())
--       print('✅ Seed complete')
--       await conn.close()
--   asyncio.run(run())
--   "
-- ============================================================

-- ══════════════════════════════════════════════════════════════
-- REAL IDs from database:
--   Users:
--     a1a1a1a1-0000-0000-0000-000000000001  System Admin
--     a1a1a1a1-0000-0000-0000-000000000002  Antalya Metro Moderator
--     a1a1a1a1-0000-0000-0000-000000000003  John Doe
--     a1a1a1a1-0000-0000-0000-000000000004  Jane Smith
--     a1a1a1a1-0000-0000-0000-000000000005  Kepez Municipality Officer
--     5e1c2fb3-86d3-41ee-9fc1-86a97f084a71  altug
--   Categories: 1=Pothole 5=Flooding 6=Road Accident 7=Obstacle 9=Damaged Sidewalk
--   Municipalities: 2=Kepez 3=Muratpaşa 4=Konyaaltı 8=Döşemealtı 9=Aksu(as Lara)
-- ══════════════════════════════════════════════════════════════

-- ── 25 Incidents ───────────────────────────────────────────
INSERT INTO "Incidents"
  ("Id","ReporterUserId","CategoryId","MunicipalityId",
   "Title","Description","Location","Status","CreatedAt")
VALUES

-- ═══ MURATPAŞA — Municipality 3 (5 incidents) ═══
('f6f6f6f6-0000-0000-0000-000000000001',
 'a1a1a1a1-0000-0000-0000-000000000003', 1, 3,
 'Büyük Çukur — Işıklar Caddesi',
 'Işıklar Caddesi üzerinde araç lastiği yırtan derin çukur. Çap yaklaşık 80 cm.',
 ST_SetSRID(ST_MakePoint(30.7135, 36.8870), 4326),
 'Verified','2026-02-20T08:30:00Z'),

('f6f6f6f6-0000-0000-0000-000000000002',
 'a1a1a1a1-0000-0000-0000-000000000004', 9, 3,
 'Kaldırım Çökmesi — Cumhuriyet Mahallesi',
 'Cumhuriyet Mahallesi yaya kaldırımı çökmüş, yayalar yoldan yürümek zorunda.',
 ST_SetSRID(ST_MakePoint(30.7050, 36.8830), 4326),
 'Pending','2026-02-25T10:15:00Z'),

('f6f6f6f6-0000-0000-0000-000000000003',
 '5e1c2fb3-86d3-41ee-9fc1-86a97f084a71', 6, 3,
 'Trafik Kazası — Aspendos Bulvarı',
 'İki araçlı maddi hasarlı kaza. Kavşak trafiği aksıyor.',
 ST_SetSRID(ST_MakePoint(30.7280, 36.8900), 4326),
 'Resolved','2026-03-01T07:45:00Z'),

('f6f6f6f6-0000-0000-0000-000000000004',
 'a1a1a1a1-0000-0000-0000-000000000003', 5, 3,
 'Su Baskını — Kışla Mahallesi',
 'Yoğun yağış sonrası alt geçit tamamen su altında kaldı.',
 ST_SetSRID(ST_MakePoint(30.7190, 36.8810), 4326),
 'Verified','2026-03-02T14:20:00Z'),

('f6f6f6f6-0000-0000-0000-000000000005',
 'a1a1a1a1-0000-0000-0000-000000000005', 7, 3,
 'Yola Düşen Ağaç — Güllük Caddesi',
 'Fırtınada kırılan ağaç dalı yol ortasını kapattı.',
 ST_SetSRID(ST_MakePoint(30.7100, 36.8850), 4326),
 'Disputed','2026-03-03T09:00:00Z'),

-- ═══ KONYAALTI — Municipality 4 (5 incidents) ═══
('f6f6f6f6-0000-0000-0000-000000000006',
 'a1a1a1a1-0000-0000-0000-000000000004', 1, 4,
 'Çoklu Çukur — Uncalı Mahallesi',
 'Uncalı girişinde art arda 4 çukur, sürücüler slalom yapıyor.',
 ST_SetSRID(ST_MakePoint(30.6320, 36.8920), 4326),
 'Verified','2026-02-18T11:00:00Z'),

('f6f6f6f6-0000-0000-0000-000000000007',
 'a1a1a1a1-0000-0000-0000-000000000003', 5, 4,
 'Sahil Yolu Su Baskını — Konyaaltı Plajı',
 'Plaj yolunda kanalizasyon taşması, koku ve hijyen sorunu.',
 ST_SetSRID(ST_MakePoint(30.6400, 36.8650), 4326),
 'Pending','2026-02-22T16:30:00Z'),

('f6f6f6f6-0000-0000-0000-000000000008',
 '5e1c2fb3-86d3-41ee-9fc1-86a97f084a71', 9, 4,
 'Yıkık Kaldırım — Arapsuyu',
 'Arapsuyu esnaf bölgesinde kaldırım taşları tamamen dağılmış.',
 ST_SetSRID(ST_MakePoint(30.6280, 36.8780), 4326),
 'Verified','2026-02-28T09:45:00Z'),

('f6f6f6f6-0000-0000-0000-000000000009',
 'a1a1a1a1-0000-0000-0000-000000000005', 7, 4,
 'İnşaat Molozları — Liman Mahallesi',
 'İnşaat artıkları yolun yarısını kaplamış, tek şerit geçiş var.',
 ST_SetSRID(ST_MakePoint(30.6100, 36.8710), 4326),
 'Pending','2026-03-03T08:10:00Z'),

('f6f6f6f6-0000-0000-0000-000000000010',
 'a1a1a1a1-0000-0000-0000-000000000004', 6, 4,
 'Motosiklet Kazası — Sakıp Sabancı Bulvarı',
 'Motosiklet kayarak refüje çarpmış. Ambulans bekleniyor.',
 ST_SetSRID(ST_MakePoint(30.6200, 36.8690), 4326),
 'Resolved','2026-03-04T19:15:00Z'),

-- ═══ KEPEZ — Municipality 2 (5 incidents) ═══
('f6f6f6f6-0000-0000-0000-000000000011',
 'a1a1a1a1-0000-0000-0000-000000000003', 1, 2,
 'Çukur — Varsak Sanayi Yolu',
 'Ağır vasıta trafiğinden asfalt çökmesi. Derinlik ~20 cm.',
 ST_SetSRID(ST_MakePoint(30.7450, 36.9350), 4326),
 'Pending','2026-02-15T07:00:00Z'),

('f6f6f6f6-0000-0000-0000-000000000012',
 'a1a1a1a1-0000-0000-0000-000000000005', 7, 2,
 'Terk Edilmiş Araç — Şafak Mahallesi',
 'Yol ortasına bırakılmış hurda araç trafiği engelliyor.',
 ST_SetSRID(ST_MakePoint(30.7350, 36.9410), 4326),
 'Verified','2026-02-19T13:30:00Z'),

('f6f6f6f6-0000-0000-0000-000000000013',
 '5e1c2fb3-86d3-41ee-9fc1-86a97f084a71', 5, 2,
 'Dere Taşkını — Kepez Santral Bölgesi',
 'Yağmur sonrası dere taşarak yolu kapattı.',
 ST_SetSRID(ST_MakePoint(30.7500, 36.9500), 4326),
 'Disputed','2026-02-23T15:00:00Z'),

('f6f6f6f6-0000-0000-0000-000000000014',
 'a1a1a1a1-0000-0000-0000-000000000004', 9, 2,
 'Hasarlı Kaldırım — Fabrikalar Mahallesi',
 'Ağaç kökleri kaldırımı kaldırmış, tekerlekli sandalye geçemiyor.',
 ST_SetSRID(ST_MakePoint(30.7300, 36.9280), 4326),
 'Resolved','2026-03-01T10:20:00Z'),

('f6f6f6f6-0000-0000-0000-000000000015',
 'a1a1a1a1-0000-0000-0000-000000000003', 6, 2,
 'Okul Önü Kaza — Kepez Anadolu Lisesi',
 'Okul servisinin karıştığı zincirleme kaza.',
 ST_SetSRID(ST_MakePoint(30.7400, 36.9370), 4326),
 'Verified','2026-03-02T08:00:00Z'),

-- ═══ AKSU (as Lara district) — Municipality 9 (5 incidents) ═══
('f6f6f6f6-0000-0000-0000-000000000016',
 'a1a1a1a1-0000-0000-0000-000000000005', 1, 9,
 'Otel Bölgesi Çukur — Lara Turizm Yolu',
 '5 yıldızlı oteller bölgesinde turistlerin şikayet ettiği büyük çukur.',
 ST_SetSRID(ST_MakePoint(30.7650, 36.8610), 4326),
 'Pending','2026-02-17T12:00:00Z'),

('f6f6f6f6-0000-0000-0000-000000000017',
 '5e1c2fb3-86d3-41ee-9fc1-86a97f084a71', 7, 9,
 'Reklam Panosu Devrilmesi — Lara Caddesi',
 'Fırtınada devrilmiş reklam panosu yolu daraltıyor.',
 ST_SetSRID(ST_MakePoint(30.7580, 36.8580), 4326),
 'Verified','2026-02-21T14:45:00Z'),

('f6f6f6f6-0000-0000-0000-000000000018',
 'a1a1a1a1-0000-0000-0000-000000000003', 5, 9,
 'Kanalizasyon Taşması — Güzeloba',
 'Güzeloba ana caddesinde kanalizasyon taşması, trafik tek yönlü.',
 ST_SetSRID(ST_MakePoint(30.7700, 36.8630), 4326),
 'Disputed','2026-02-26T17:00:00Z'),

('f6f6f6f6-0000-0000-0000-000000000019',
 'a1a1a1a1-0000-0000-0000-000000000004', 9, 9,
 'Kırık Kaldırım — Kundu',
 'Kundu turistik bölgesinde kaldırım levhaları kırık.',
 ST_SetSRID(ST_MakePoint(30.7750, 36.8560), 4326),
 'Resolved','2026-03-01T11:30:00Z'),

('f6f6f6f6-0000-0000-0000-000000000020',
 'a1a1a1a1-0000-0000-0000-000000000005', 6, 9,
 'Bisiklet Kazası — Lara Sahil Yolu',
 'Bisikletçi ve yaya çarpışması, hasta düşmüş.',
 ST_SetSRID(ST_MakePoint(30.7620, 36.8595), 4326),
 'Pending','2026-03-04T18:00:00Z'),

-- ═══ DÖŞEMEALTI — Municipality 8 (5 incidents) ═══
('f6f6f6f6-0000-0000-0000-000000000021',
 'a1a1a1a1-0000-0000-0000-000000000004', 1, 8,
 'Çukur — Çıplaklı Köy Yolu',
 'Köy yolunda kamyon geçişinden oluşan derin çukur.',
 ST_SetSRID(ST_MakePoint(30.6050, 37.0200), 4326),
 'Verified','2026-02-16T06:30:00Z'),

('f6f6f6f6-0000-0000-0000-000000000022',
 'a1a1a1a1-0000-0000-0000-000000000003', 7, 8,
 'Kaya Düşmesi — Termessos Yolu',
 'Dağ eteklerinden düşen kayalar yolu kapatmış.',
 ST_SetSRID(ST_MakePoint(30.5900, 37.0350), 4326),
 'Pending','2026-02-24T09:20:00Z'),

('f6f6f6f6-0000-0000-0000-000000000023',
 '5e1c2fb3-86d3-41ee-9fc1-86a97f084a71', 5, 8,
 'Dere Taşkını — Yağca Mahallesi',
 'Yağmur suları tarla alanını ve yan yolu bastı.',
 ST_SetSRID(ST_MakePoint(30.6150, 37.0100), 4326),
 'Resolved','2026-02-27T13:00:00Z'),

('f6f6f6f6-0000-0000-0000-000000000024',
 'a1a1a1a1-0000-0000-0000-000000000005', 6, 8,
 'Traktör Kazası — D-685 Karayolu',
 'Traktör devrilmiş, yol tek şeritten geçiş yapılıyor.',
 ST_SetSRID(ST_MakePoint(30.6250, 37.0050), 4326),
 'Verified','2026-03-02T16:40:00Z'),

('f6f6f6f6-0000-0000-0000-000000000025',
 'a1a1a1a1-0000-0000-0000-000000000004', 9, 8,
 'Hasar Görmüş Yaya Yolu — Bademağacı',
 'Bademağacı mahallesi yaya geçidinde kaldırım çökmeleri.',
 ST_SetSRID(ST_MakePoint(30.5980, 37.0280), 4326),
 'Disputed','2026-03-05T10:50:00Z')

ON CONFLICT ("Id") DO NOTHING;


-- ── Verifications (62 rows — diverse positive/negative mix) ──
INSERT INTO "Verifications" ("IncidentId","UserId","IsPositive","CreatedAt")
SELECT v."IncidentId", v."UserId", v."IsPositive", v."CreatedAt"
FROM (VALUES
-- Muratpaşa incidents
('f6f6f6f6-0000-0000-0000-000000000001'::uuid,'a1a1a1a1-0000-0000-0000-000000000004'::uuid,true,  '2026-02-20T10:00:00Z'::timestamptz),
('f6f6f6f6-0000-0000-0000-000000000001','5e1c2fb3-86d3-41ee-9fc1-86a97f084a71',true, '2026-02-20T11:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000001','a1a1a1a1-0000-0000-0000-000000000005',true, '2026-02-20T14:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000002','a1a1a1a1-0000-0000-0000-000000000003',true, '2026-02-25T12:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000002','5e1c2fb3-86d3-41ee-9fc1-86a97f084a71',true, '2026-02-25T15:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000003','a1a1a1a1-0000-0000-0000-000000000003',true, '2026-03-01T09:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000003','a1a1a1a1-0000-0000-0000-000000000004',true, '2026-03-01T10:30:00Z'),
('f6f6f6f6-0000-0000-0000-000000000003','a1a1a1a1-0000-0000-0000-000000000005',true, '2026-03-01T12:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000004','a1a1a1a1-0000-0000-0000-000000000004',true, '2026-03-02T16:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000004','a1a1a1a1-0000-0000-0000-000000000005',true, '2026-03-02T17:30:00Z'),
('f6f6f6f6-0000-0000-0000-000000000004','5e1c2fb3-86d3-41ee-9fc1-86a97f084a71',true, '2026-03-02T19:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000005','a1a1a1a1-0000-0000-0000-000000000003',true, '2026-03-03T11:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000005','a1a1a1a1-0000-0000-0000-000000000004',false,'2026-03-03T12:00:00Z'),

-- Konyaaltı incidents
('f6f6f6f6-0000-0000-0000-000000000006','a1a1a1a1-0000-0000-0000-000000000003',true, '2026-02-18T14:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000006','a1a1a1a1-0000-0000-0000-000000000005',true, '2026-02-18T16:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000006','5e1c2fb3-86d3-41ee-9fc1-86a97f084a71',true, '2026-02-19T09:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000007','a1a1a1a1-0000-0000-0000-000000000004',true, '2026-02-22T18:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000007','a1a1a1a1-0000-0000-0000-000000000005',true, '2026-02-23T08:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000008','a1a1a1a1-0000-0000-0000-000000000003',true, '2026-02-28T12:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000008','a1a1a1a1-0000-0000-0000-000000000004',true, '2026-02-28T14:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000008','a1a1a1a1-0000-0000-0000-000000000005',true, '2026-03-01T08:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000009','5e1c2fb3-86d3-41ee-9fc1-86a97f084a71',true, '2026-03-03T10:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000009','a1a1a1a1-0000-0000-0000-000000000003',false,'2026-03-03T11:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000010','a1a1a1a1-0000-0000-0000-000000000003',true, '2026-03-04T20:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000010','5e1c2fb3-86d3-41ee-9fc1-86a97f084a71',true, '2026-03-04T21:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000010','a1a1a1a1-0000-0000-0000-000000000005',true, '2026-03-05T07:00:00Z'),

-- Kepez incidents
('f6f6f6f6-0000-0000-0000-000000000011','a1a1a1a1-0000-0000-0000-000000000004',true, '2026-02-15T09:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000011','5e1c2fb3-86d3-41ee-9fc1-86a97f084a71',true, '2026-02-15T10:30:00Z'),
('f6f6f6f6-0000-0000-0000-000000000012','a1a1a1a1-0000-0000-0000-000000000003',true, '2026-02-19T15:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000012','a1a1a1a1-0000-0000-0000-000000000004',true, '2026-02-19T16:30:00Z'),
('f6f6f6f6-0000-0000-0000-000000000012','5e1c2fb3-86d3-41ee-9fc1-86a97f084a71',true, '2026-02-20T08:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000013','a1a1a1a1-0000-0000-0000-000000000004',true, '2026-02-23T17:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000013','a1a1a1a1-0000-0000-0000-000000000005',false,'2026-02-24T09:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000014','a1a1a1a1-0000-0000-0000-000000000003',true, '2026-03-01T12:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000014','5e1c2fb3-86d3-41ee-9fc1-86a97f084a71',true, '2026-03-01T14:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000015','a1a1a1a1-0000-0000-0000-000000000004',true, '2026-03-02T10:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000015','a1a1a1a1-0000-0000-0000-000000000005',true, '2026-03-02T11:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000015','5e1c2fb3-86d3-41ee-9fc1-86a97f084a71',true, '2026-03-02T13:00:00Z'),

-- Aksu/Lara incidents
('f6f6f6f6-0000-0000-0000-000000000016','a1a1a1a1-0000-0000-0000-000000000003',true, '2026-02-17T14:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000016','a1a1a1a1-0000-0000-0000-000000000004',true, '2026-02-17T16:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000017','a1a1a1a1-0000-0000-0000-000000000003',true, '2026-02-21T16:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000017','a1a1a1a1-0000-0000-0000-000000000005',true, '2026-02-21T18:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000017','a1a1a1a1-0000-0000-0000-000000000004',true, '2026-02-22T08:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000018','a1a1a1a1-0000-0000-0000-000000000005',true, '2026-02-26T19:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000018','a1a1a1a1-0000-0000-0000-000000000004',false,'2026-02-27T08:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000019','a1a1a1a1-0000-0000-0000-000000000003',true, '2026-03-01T13:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000019','5e1c2fb3-86d3-41ee-9fc1-86a97f084a71',true, '2026-03-01T15:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000019','a1a1a1a1-0000-0000-0000-000000000005',true, '2026-03-02T08:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000020','a1a1a1a1-0000-0000-0000-000000000003',true, '2026-03-04T19:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000020','a1a1a1a1-0000-0000-0000-000000000004',true, '2026-03-04T20:30:00Z'),

-- Döşemealtı incidents
('f6f6f6f6-0000-0000-0000-000000000021','a1a1a1a1-0000-0000-0000-000000000003',true, '2026-02-16T08:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000021','a1a1a1a1-0000-0000-0000-000000000005',true, '2026-02-16T10:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000021','5e1c2fb3-86d3-41ee-9fc1-86a97f084a71',true, '2026-02-16T12:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000022','a1a1a1a1-0000-0000-0000-000000000004',true, '2026-02-24T11:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000022','5e1c2fb3-86d3-41ee-9fc1-86a97f084a71',true, '2026-02-24T13:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000023','a1a1a1a1-0000-0000-0000-000000000005',true, '2026-02-27T15:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000023','a1a1a1a1-0000-0000-0000-000000000003',true, '2026-02-28T07:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000023','a1a1a1a1-0000-0000-0000-000000000004',true, '2026-02-28T09:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000024','a1a1a1a1-0000-0000-0000-000000000003',true, '2026-03-02T18:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000024','5e1c2fb3-86d3-41ee-9fc1-86a97f084a71',true, '2026-03-02T19:30:00Z'),
('f6f6f6f6-0000-0000-0000-000000000024','a1a1a1a1-0000-0000-0000-000000000004',true, '2026-03-03T07:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000025','a1a1a1a1-0000-0000-0000-000000000003',true, '2026-03-05T12:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000025','a1a1a1a1-0000-0000-0000-000000000005',false,'2026-03-05T14:00:00Z')
) AS v("IncidentId","UserId","IsPositive","CreatedAt")
WHERE NOT EXISTS (
  SELECT 1 FROM "Verifications" vv
  WHERE vv."IncidentId" = v."IncidentId" AND vv."UserId" = v."UserId"
);


-- ── Photos (25 rows — one per incident min) ───────────────
INSERT INTO "IncidentPhotos" ("IncidentId","BlobUrl")
SELECT p."IncidentId", p."BlobUrl"
FROM (VALUES
('f6f6f6f6-0000-0000-0000-000000000001'::uuid,'https://storage.saferoad.app/antalya/muratpasa_cukur_01.jpg'),
('f6f6f6f6-0000-0000-0000-000000000002','https://storage.saferoad.app/antalya/muratpasa_kaldirim_01.jpg'),
('f6f6f6f6-0000-0000-0000-000000000003','https://storage.saferoad.app/antalya/muratpasa_kaza_01.jpg'),
('f6f6f6f6-0000-0000-0000-000000000003','https://storage.saferoad.app/antalya/muratpasa_kaza_02.jpg'),
('f6f6f6f6-0000-0000-0000-000000000004','https://storage.saferoad.app/antalya/muratpasa_su_01.jpg'),
('f6f6f6f6-0000-0000-0000-000000000005','https://storage.saferoad.app/antalya/muratpasa_agac_01.jpg'),
('f6f6f6f6-0000-0000-0000-000000000006','https://storage.saferoad.app/antalya/konyaalti_cukur_01.jpg'),
('f6f6f6f6-0000-0000-0000-000000000007','https://storage.saferoad.app/antalya/konyaalti_su_01.jpg'),
('f6f6f6f6-0000-0000-0000-000000000008','https://storage.saferoad.app/antalya/konyaalti_kaldirim_01.jpg'),
('f6f6f6f6-0000-0000-0000-000000000009','https://storage.saferoad.app/antalya/konyaalti_moloz_01.jpg'),
('f6f6f6f6-0000-0000-0000-000000000010','https://storage.saferoad.app/antalya/konyaalti_kaza_01.jpg'),
('f6f6f6f6-0000-0000-0000-000000000011','https://storage.saferoad.app/antalya/kepez_cukur_01.jpg'),
('f6f6f6f6-0000-0000-0000-000000000012','https://storage.saferoad.app/antalya/kepez_hurda_01.jpg'),
('f6f6f6f6-0000-0000-0000-000000000012','https://storage.saferoad.app/antalya/kepez_hurda_02.jpg'),
('f6f6f6f6-0000-0000-0000-000000000013','https://storage.saferoad.app/antalya/kepez_dere_01.jpg'),
('f6f6f6f6-0000-0000-0000-000000000014','https://storage.saferoad.app/antalya/kepez_kaldirim_01.jpg'),
('f6f6f6f6-0000-0000-0000-000000000015','https://storage.saferoad.app/antalya/kepez_kaza_01.jpg'),
('f6f6f6f6-0000-0000-0000-000000000016','https://storage.saferoad.app/antalya/lara_cukur_01.jpg'),
('f6f6f6f6-0000-0000-0000-000000000017','https://storage.saferoad.app/antalya/lara_pano_01.jpg'),
('f6f6f6f6-0000-0000-0000-000000000018','https://storage.saferoad.app/antalya/lara_kanalizasyon_01.jpg'),
('f6f6f6f6-0000-0000-0000-000000000019','https://storage.saferoad.app/antalya/lara_kaldirim_01.jpg'),
('f6f6f6f6-0000-0000-0000-000000000020','https://storage.saferoad.app/antalya/lara_bisiklet_01.jpg'),
('f6f6f6f6-0000-0000-0000-000000000021','https://storage.saferoad.app/antalya/dosemealti_cukur_01.jpg'),
('f6f6f6f6-0000-0000-0000-000000000022','https://storage.saferoad.app/antalya/dosemealti_kaya_01.jpg'),
('f6f6f6f6-0000-0000-0000-000000000022','https://storage.saferoad.app/antalya/dosemealti_kaya_02.jpg'),
('f6f6f6f6-0000-0000-0000-000000000023','https://storage.saferoad.app/antalya/dosemealti_taskin_01.jpg'),
('f6f6f6f6-0000-0000-0000-000000000024','https://storage.saferoad.app/antalya/dosemealti_traktor_01.jpg'),
('f6f6f6f6-0000-0000-0000-000000000025','https://storage.saferoad.app/antalya/dosemealti_kaldirim_01.jpg')
) AS p("IncidentId","BlobUrl")
WHERE NOT EXISTS (
  SELECT 1 FROM "IncidentPhotos" ip
  WHERE ip."IncidentId" = p."IncidentId" AND ip."BlobUrl" = p."BlobUrl"
);


-- ── Comments (15 rows) ────────────────────────────────────
INSERT INTO "Comments" ("IncidentId","UserId","Content","CreatedAt")
SELECT c."IncidentId", c."UserId", c."Content", c."CreatedAt"
FROM (VALUES
('f6f6f6f6-0000-0000-0000-000000000001'::uuid,'a1a1a1a1-0000-0000-0000-000000000004'::uuid,
 'Dün buradan geçtim, gerçekten tehlikeli. Lastik patlatabilir.','2026-02-20T12:00:00Z'::timestamptz),
('f6f6f6f6-0000-0000-0000-000000000001','5e1c2fb3-86d3-41ee-9fc1-86a97f084a71',
 'Belediyeye de bildirdim, 1 haftadır ilgilenilmedi.','2026-02-21T09:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000003','a1a1a1a1-0000-0000-0000-000000000003',
 'Kaza temizlendi ama kavşak hâlâ riskli.','2026-03-01T15:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000004','a1a1a1a1-0000-0000-0000-000000000005',
 'Alt geçit kullanılamaz durumda, alternatif güzergah kullanın.','2026-03-02T17:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000006','a1a1a1a1-0000-0000-0000-000000000003',
 '4 çukurun hepsini tek tek fotoğrafladım. Ciddi durum.','2026-02-18T15:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000007','a1a1a1a1-0000-0000-0000-000000000004',
 'Koku dayanılmaz seviyede, turist bölgesinde utanç verici.','2026-02-23T10:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000010','a1a1a1a1-0000-0000-0000-000000000005',
 'Motosikletçi hastaneye kaldırıldı, geçmiş olsun.','2026-03-04T22:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000011','a1a1a1a1-0000-0000-0000-000000000004',
 'Sanayi bölgesindeki yollar genel olarak çok kötü.','2026-02-15T11:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000013','5e1c2fb3-86d3-41ee-9fc1-86a97f084a71',
 'Dere taşkını gerçekten var mı, ben geçen hafta göremedim.','2026-02-24T10:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000015','a1a1a1a1-0000-0000-0000-000000000003',
 'Okul önünde hız bumpu ve tabela şart!','2026-03-02T12:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000016','a1a1a1a1-0000-0000-0000-000000000003',
 'Turistler araçlarını çizmiş, otel yönetimi de şikayetçi.','2026-02-18T10:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000018','5e1c2fb3-86d3-41ee-9fc1-86a97f084a71',
 'Sadece taşma değil, asfalt da kalkıyor.','2026-02-27T09:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000021','a1a1a1a1-0000-0000-0000-000000000005',
 'Kamyonlar ağırlık sınırını sürekli aşıyor.','2026-02-16T10:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000022','a1a1a1a1-0000-0000-0000-000000000004',
 'Termessos yolu zaten tehlikeli, kayalar durumu iyice kötüleştirdi.','2026-02-24T14:00:00Z'),
('f6f6f6f6-0000-0000-0000-000000000024','5e1c2fb3-86d3-41ee-9fc1-86a97f084a71',
 'Traktör hâlâ kaldırılmadı, 2 gün oldu.','2026-03-04T08:00:00Z')
) AS c("IncidentId","UserId","Content","CreatedAt")
WHERE NOT EXISTS (
  SELECT 1 FROM "Comments" cc
  WHERE cc."IncidentId" = c."IncidentId" AND cc."UserId" = c."UserId" AND cc."Content" = c."Content"
);