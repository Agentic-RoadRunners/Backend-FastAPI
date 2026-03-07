-- ============================================================
-- SafeRoad Mock Data Seed Script
-- 20+ Antalya incidents across 4 municipalities, 5 categories
-- Idempotent: uses ON CONFLICT / WHERE NOT EXISTS guards
-- ============================================================

-- ── Mock Users ──────────────────────────────────────────────
INSERT INTO "Users" ("Id", "Email", "PasswordHash", "FullName", "TrustScore", "Status", "CreatedAt")
VALUES
  ('c3c3c3c3-0000-0000-0000-000000000001', 'ahmet.yilmaz@gmail.com',
   '$2a$11$mockhashmockhashmockhashmockhashmockhashmockhash01', 'Ahmet Yılmaz', 120, 'Active', '2026-01-10T08:00:00Z'),
  ('c3c3c3c3-0000-0000-0000-000000000002', 'elif.kaya@gmail.com',
   '$2a$11$mockhashmockhashmockhashmockhashmockhashmockhash02', 'Elif Kaya', 85, 'Active', '2026-01-15T10:30:00Z'),
  ('c3c3c3c3-0000-0000-0000-000000000003', 'mehmet.demir@gmail.com',
   '$2a$11$mockhashmockhashmockhashmockhashmockhashmockhash03', 'Mehmet Demir', 60, 'Active', '2026-02-01T14:00:00Z')
ON CONFLICT ("Id") DO NOTHING;

-- Assign User role (Id=1) to mock users
INSERT INTO "UserRoles" ("UserId", "RoleId")
VALUES
  ('c3c3c3c3-0000-0000-0000-000000000001', 1),
  ('c3c3c3c3-0000-0000-0000-000000000002', 1),
  ('c3c3c3c3-0000-0000-0000-000000000003', 1)
ON CONFLICT ("UserId", "RoleId") DO NOTHING;

-- ── 22 Incidents ────────────────────────────────────────────
-- Municipalities: 2=Kepez, 3=Muratpaşa, 4=Konyaaltı, 8=Döşemealtı
-- Categories: 1=Pothole, 5=Flooding, 6=Road Accident, 7=Obstacle on Road, 9=Damaged Sidewalk
-- Reporters: c3-01 (Ahmet), c3-02 (Elif), c3-03 (Mehmet), a1-03 (John), a1-04 (Jane)

INSERT INTO "Incidents" ("Id", "ReporterUserId", "CategoryId", "MunicipalityId", "Title", "Description", "Location", "Status", "CreatedAt")
VALUES
  -- ── Kepez (MunicipalityId = 2) ── 6 incidents
  ('d4d4d4d4-0000-0000-0000-000000000001',
   'c3c3c3c3-0000-0000-0000-000000000001', 1, 2,
   'Kepez Ankara Caddesi Çukur',
   'Ankara Caddesi üzerinde araç lastiği patlatan derin çukur. Yaklaşık 40cm çapında.',
   ST_SetSRID(ST_MakePoint(30.7250, 37.0050), 4326), 'Pending', '2026-02-15T09:00:00Z'),

  ('d4d4d4d4-0000-0000-0000-000000000002',
   'c3c3c3c3-0000-0000-0000-000000000002', 5, 2,
   'Kepez Sanayi Bölgesi Su Baskını',
   'Yoğun yağış sonrası sanayi bölgesinde 30cm su birikintisi oluştu.',
   ST_SetSRID(ST_MakePoint(30.7320, 37.0120), 4326), 'Verified', '2026-02-18T14:30:00Z'),

  ('d4d4d4d4-0000-0000-0000-000000000003',
   'c3c3c3c3-0000-0000-0000-000000000003', 7, 2,
   'Kepez Fabrikalar Yolunda Engel',
   'Yolun ortasında terk edilmiş inşaat malzemesi. Trafik akışını engelliyor.',
   ST_SetSRID(ST_MakePoint(30.7180, 37.0080), 4326), 'Pending', '2026-02-20T11:15:00Z'),

  ('d4d4d4d4-0000-0000-0000-000000000004',
   'a1a1a1a1-0000-0000-0000-000000000003', 6, 2,
   'Kepez Kavşağında Kaza',
   'İki araçlı trafik kazası, yol kısmen kapalı. Cam kırıkları yolda.',
   ST_SetSRID(ST_MakePoint(30.7100, 37.0000), 4326), 'Verified', '2026-02-22T07:45:00Z'),

  ('d4d4d4d4-0000-0000-0000-000000000005',
   'c3c3c3c3-0000-0000-0000-000000000001', 9, 2,
   'Kepez Hastane Yolu Kaldırım Hasarı',
   'Hastane önündeki kaldırım çökmüş, yaya güvenliğini tehdit ediyor.',
   ST_SetSRID(ST_MakePoint(30.7210, 36.9950), 4326), 'Disputed', '2026-02-25T16:00:00Z'),

  ('d4d4d4d4-0000-0000-0000-000000000006',
   'c3c3c3c3-0000-0000-0000-000000000002', 1, 2,
   'Kepez Altınova Çukur',
   'Altınova mahallesi ara sokaklarında çok sayıda çukur mevcut.',
   ST_SetSRID(ST_MakePoint(30.7150, 37.0150), 4326), 'Resolved', '2026-01-28T10:00:00Z'),

  -- ── Muratpaşa (MunicipalityId = 3) ── 6 incidents
  ('d4d4d4d4-0000-0000-0000-000000000007',
   'a1a1a1a1-0000-0000-0000-000000000004', 1, 3,
   'Muratpaşa Atatürk Bulvarı Çukur',
   'Ana cadde üzerinde araçlar için tehlikeli çukur. Derinliği 15cm civarı.',
   ST_SetSRID(ST_MakePoint(30.7050, 36.8850), 4326), 'Pending', '2026-02-16T08:30:00Z'),

  ('d4d4d4d4-0000-0000-0000-000000000008',
   'c3c3c3c3-0000-0000-0000-000000000001', 5, 3,
   'Muratpaşa Kaleiçi Bölgesi Su Birikintisi',
   'Tarihi Kaleiçi sokaklarında drenaj yetersizliğinden dolayı su birikmesi.',
   ST_SetSRID(ST_MakePoint(30.7020, 36.8870), 4326), 'Verified', '2026-02-19T12:00:00Z'),

  ('d4d4d4d4-0000-0000-0000-000000000009',
   'c3c3c3c3-0000-0000-0000-000000000002', 6, 3,
   'Muratpaşa Lara Yolunda Kaza',
   'Lara sahil yolunda motorsiklet-araç çarpışması. Yol dar kesimde kapalı.',
   ST_SetSRID(ST_MakePoint(30.7400, 36.8600), 4326), 'Disputed', '2026-02-21T18:20:00Z'),

  ('d4d4d4d4-0000-0000-0000-000000000010',
   'c3c3c3c3-0000-0000-0000-000000000003', 7, 3,
   'Muratpaşa Işıklar Caddesi Engel',
   'Kaldırım üzerinde bırakılan elektrik direği parçaları yaya trafiğini engelliyor.',
   ST_SetSRID(ST_MakePoint(30.6980, 36.8900), 4326), 'Pending', '2026-02-23T09:00:00Z'),

  ('d4d4d4d4-0000-0000-0000-000000000011',
   'a1a1a1a1-0000-0000-0000-000000000003', 9, 3,
   'Muratpaşa Güllük Caddesi Kaldırım',
   'Güllük Caddesi kaldırımları yer yer kırık, tekerlekli sandalye erişimi zor.',
   ST_SetSRID(ST_MakePoint(30.7100, 36.8820), 4326), 'Resolved', '2026-01-30T13:00:00Z'),

  ('d4d4d4d4-0000-0000-0000-000000000012',
   'c3c3c3c3-0000-0000-0000-000000000001', 1, 3,
   'Muratpaşa Konyaaltı Kavşağı Çukur',
   'Kavşaktaki dönemeçte araçların sıklıkla çarptığı derin çukur.',
   ST_SetSRID(ST_MakePoint(30.6920, 36.8780), 4326), 'Verified', '2026-02-26T15:00:00Z'),

  -- ── Konyaaltı (MunicipalityId = 4) ── 5 incidents
  ('d4d4d4d4-0000-0000-0000-000000000013',
   'c3c3c3c3-0000-0000-0000-000000000002', 5, 4,
   'Konyaaltı Sahil Yolu Taşkını',
   'Konyaaltı sahil yolunda deniz taşması nedeniyle su baskını. Araç geçişi zor.',
   ST_SetSRID(ST_MakePoint(30.6350, 36.8680), 4326), 'Verified', '2026-02-17T16:00:00Z'),

  ('d4d4d4d4-0000-0000-0000-000000000014',
   'c3c3c3c3-0000-0000-0000-000000000003', 1, 4,
   'Konyaaltı Liman Yolu Çukur',
   'Liman bölgesi yolunda ağır araç trafiğinden kaynaklanan çukurlar.',
   ST_SetSRID(ST_MakePoint(30.6200, 36.8620), 4326), 'Pending', '2026-02-24T10:30:00Z'),

  ('d4d4d4d4-0000-0000-0000-000000000015',
   'a1a1a1a1-0000-0000-0000-000000000004', 6, 4,
   'Konyaaltı Antalya Bulvarı Kaza',
   'Antalya-Kemer yolu giriş kavşağında zincirleme kaza. 3 araç karışık.',
   ST_SetSRID(ST_MakePoint(30.5950, 36.8750), 4326), 'Disputed', '2026-02-20T08:00:00Z'),

  ('d4d4d4d4-0000-0000-0000-000000000016',
   'c3c3c3c3-0000-0000-0000-000000000001', 7, 4,
   'Konyaaltı Hurma Mahallesi Engel',
   'Hurma mahallesinde yol kenarında devrilmiş ağaç. Tek şerit kapalı.',
   ST_SetSRID(ST_MakePoint(30.6450, 36.8900), 4326), 'Resolved', '2026-02-10T12:00:00Z'),

  ('d4d4d4d4-0000-0000-0000-000000000017',
   'c3c3c3c3-0000-0000-0000-000000000002', 9, 4,
   'Konyaaltı Üniversite Yolu Kaldırım',
   'Akdeniz Üniversitesi girişindeki kaldırım hasar görmüş.',
   ST_SetSRID(ST_MakePoint(30.6550, 36.8950), 4326), 'Pending', '2026-03-01T09:00:00Z'),

  -- ── Döşemealtı (MunicipalityId = 8) ── 5 incidents
  ('d4d4d4d4-0000-0000-0000-000000000018',
   'c3c3c3c3-0000-0000-0000-000000000003', 1, 8,
   'Döşemealtı Antalya-Burdur Yolu Çukuru',
   'Antalya-Burdur karayolu üzerinde büyük çukur. TIR trafiği yoğun.',
   ST_SetSRID(ST_MakePoint(30.5800, 37.0500), 4326), 'Verified', '2026-02-14T07:00:00Z'),

  ('d4d4d4d4-0000-0000-0000-000000000019',
   'c3c3c3c3-0000-0000-0000-000000000001', 5, 8,
   'Döşemealtı Çıplaklı Mahallesi Sel',
   'Çıplaklı mahallesinde dere taşması sonucu yollar su altında.',
   ST_SetSRID(ST_MakePoint(30.6000, 37.0300), 4326), 'Disputed', '2026-02-28T20:00:00Z'),

  ('d4d4d4d4-0000-0000-0000-000000000020',
   'a1a1a1a1-0000-0000-0000-000000000003', 6, 8,
   'Döşemealtı Sanayi Kavşağı Kazası',
   'Sanayi kavşağında kamyon ile otomobil çarpışması.',
   ST_SetSRID(ST_MakePoint(30.6100, 37.0400), 4326), 'Resolved', '2026-02-08T06:30:00Z'),

  ('d4d4d4d4-0000-0000-0000-000000000021',
   'c3c3c3c3-0000-0000-0000-000000000002', 7, 8,
   'Döşemealtı Köy Yolunda Toprak Kayması',
   'Yağmur sonrası köy yoluna toprak kaymış, tek şeritli geçiş.',
   ST_SetSRID(ST_MakePoint(30.5700, 37.0600), 4326), 'Pending', '2026-03-02T11:00:00Z'),

  ('d4d4d4d4-0000-0000-0000-000000000022',
   'c3c3c3c3-0000-0000-0000-000000000003', 9, 8,
   'Döşemealtı Yeni Yerleşim Kaldırım',
   'Yeni yapılan yerleşim alanında kaldırımlar tamamlanmamış.',
   ST_SetSRID(ST_MakePoint(30.5900, 37.0200), 4326), 'Resolved', '2026-01-20T15:00:00Z')
ON CONFLICT ("Id") DO NOTHING;

-- ── Verifications ───────────────────────────────────────────
-- Mix of positive and negative verifications, ~2-4 per incident
INSERT INTO "Verifications" ("IncidentId", "UserId", "IsPositive", "CreatedAt")
SELECT v."IncidentId", v."UserId", v."IsPositive", v."CreatedAt"::timestamptz
FROM (VALUES
  -- Incident 01 (Pending) - 3 verifications
  ('d4d4d4d4-0000-0000-0000-000000000001'::uuid, 'c3c3c3c3-0000-0000-0000-000000000002'::uuid, true,  '2026-02-15T12:00:00Z'),
  ('d4d4d4d4-0000-0000-0000-000000000001'::uuid, 'a1a1a1a1-0000-0000-0000-000000000004'::uuid, true,  '2026-02-15T14:00:00Z'),
  ('d4d4d4d4-0000-0000-0000-000000000001'::uuid, 'c3c3c3c3-0000-0000-0000-000000000003'::uuid, false, '2026-02-16T08:00:00Z'),
  -- Incident 02 (Verified) - 3 verifications
  ('d4d4d4d4-0000-0000-0000-000000000002'::uuid, 'c3c3c3c3-0000-0000-0000-000000000001'::uuid, true,  '2026-02-18T16:00:00Z'),
  ('d4d4d4d4-0000-0000-0000-000000000002'::uuid, 'a1a1a1a1-0000-0000-0000-000000000003'::uuid, true,  '2026-02-18T18:00:00Z'),
  ('d4d4d4d4-0000-0000-0000-000000000002'::uuid, 'a1a1a1a1-0000-0000-0000-000000000004'::uuid, true,  '2026-02-19T09:00:00Z'),
  -- Incident 03 (Pending) - 2 verifications
  ('d4d4d4d4-0000-0000-0000-000000000003'::uuid, 'c3c3c3c3-0000-0000-0000-000000000001'::uuid, true,  '2026-02-20T14:00:00Z'),
  ('d4d4d4d4-0000-0000-0000-000000000003'::uuid, 'c3c3c3c3-0000-0000-0000-000000000002'::uuid, false, '2026-02-21T10:00:00Z'),
  -- Incident 04 (Verified) - 3 verifications
  ('d4d4d4d4-0000-0000-0000-000000000004'::uuid, 'c3c3c3c3-0000-0000-0000-000000000001'::uuid, true,  '2026-02-22T10:00:00Z'),
  ('d4d4d4d4-0000-0000-0000-000000000004'::uuid, 'c3c3c3c3-0000-0000-0000-000000000002'::uuid, true,  '2026-02-22T12:00:00Z'),
  ('d4d4d4d4-0000-0000-0000-000000000004'::uuid, 'c3c3c3c3-0000-0000-0000-000000000003'::uuid, true,  '2026-02-22T14:00:00Z'),
  -- Incident 05 (Disputed) - 4 verifications (mixed)
  ('d4d4d4d4-0000-0000-0000-000000000005'::uuid, 'c3c3c3c3-0000-0000-0000-000000000002'::uuid, true,  '2026-02-25T18:00:00Z'),
  ('d4d4d4d4-0000-0000-0000-000000000005'::uuid, 'a1a1a1a1-0000-0000-0000-000000000003'::uuid, false, '2026-02-25T20:00:00Z'),
  ('d4d4d4d4-0000-0000-0000-000000000005'::uuid, 'a1a1a1a1-0000-0000-0000-000000000004'::uuid, false, '2026-02-26T08:00:00Z'),
  ('d4d4d4d4-0000-0000-0000-000000000005'::uuid, 'c3c3c3c3-0000-0000-0000-000000000003'::uuid, true,  '2026-02-26T10:00:00Z'),
  -- Incident 07 (Pending) - 2 verifications
  ('d4d4d4d4-0000-0000-0000-000000000007'::uuid, 'c3c3c3c3-0000-0000-0000-000000000001'::uuid, true,  '2026-02-16T11:00:00Z'),
  ('d4d4d4d4-0000-0000-0000-000000000007'::uuid, 'c3c3c3c3-0000-0000-0000-000000000003'::uuid, true,  '2026-02-17T09:00:00Z'),
  -- Incident 08 (Verified) - 3 verifications
  ('d4d4d4d4-0000-0000-0000-000000000008'::uuid, 'c3c3c3c3-0000-0000-0000-000000000002'::uuid, true,  '2026-02-19T14:00:00Z'),
  ('d4d4d4d4-0000-0000-0000-000000000008'::uuid, 'a1a1a1a1-0000-0000-0000-000000000003'::uuid, true,  '2026-02-19T16:00:00Z'),
  ('d4d4d4d4-0000-0000-0000-000000000008'::uuid, 'c3c3c3c3-0000-0000-0000-000000000003'::uuid, true,  '2026-02-20T08:00:00Z'),
  -- Incident 09 (Disputed) - 3 verifications (mixed)
  ('d4d4d4d4-0000-0000-0000-000000000009'::uuid, 'c3c3c3c3-0000-0000-0000-000000000001'::uuid, false, '2026-02-22T08:00:00Z'),
  ('d4d4d4d4-0000-0000-0000-000000000009'::uuid, 'c3c3c3c3-0000-0000-0000-000000000003'::uuid, true,  '2026-02-22T10:00:00Z'),
  ('d4d4d4d4-0000-0000-0000-000000000009'::uuid, 'a1a1a1a1-0000-0000-0000-000000000004'::uuid, false, '2026-02-22T12:00:00Z'),
  -- Incident 13 (Verified) - 2 verifications
  ('d4d4d4d4-0000-0000-0000-000000000013'::uuid, 'c3c3c3c3-0000-0000-0000-000000000001'::uuid, true,  '2026-02-17T18:00:00Z'),
  ('d4d4d4d4-0000-0000-0000-000000000013'::uuid, 'c3c3c3c3-0000-0000-0000-000000000003'::uuid, true,  '2026-02-18T08:00:00Z'),
  -- Incident 18 (Verified) - 2 verifications
  ('d4d4d4d4-0000-0000-0000-000000000018'::uuid, 'c3c3c3c3-0000-0000-0000-000000000002'::uuid, true,  '2026-02-14T10:00:00Z'),
  ('d4d4d4d4-0000-0000-0000-000000000018'::uuid, 'a1a1a1a1-0000-0000-0000-000000000004'::uuid, true,  '2026-02-14T14:00:00Z'),
  -- Incident 19 (Disputed) - 3 verifications
  ('d4d4d4d4-0000-0000-0000-000000000019'::uuid, 'c3c3c3c3-0000-0000-0000-000000000002'::uuid, false, '2026-02-28T22:00:00Z'),
  ('d4d4d4d4-0000-0000-0000-000000000019'::uuid, 'c3c3c3c3-0000-0000-0000-000000000003'::uuid, true,  '2026-03-01T08:00:00Z'),
  ('d4d4d4d4-0000-0000-0000-000000000019'::uuid, 'a1a1a1a1-0000-0000-0000-000000000003'::uuid, false, '2026-03-01T10:00:00Z'),
  -- Incident 12 (Verified) - 2 verifications
  ('d4d4d4d4-0000-0000-0000-000000000012'::uuid, 'c3c3c3c3-0000-0000-0000-000000000002'::uuid, true,  '2026-02-27T08:00:00Z'),
  ('d4d4d4d4-0000-0000-0000-000000000012'::uuid, 'c3c3c3c3-0000-0000-0000-000000000003'::uuid, true,  '2026-02-27T12:00:00Z')
) AS v("IncidentId", "UserId", "IsPositive", "CreatedAt")
WHERE NOT EXISTS (
  SELECT 1 FROM "Verifications" vx
  WHERE vx."IncidentId" = v."IncidentId" AND vx."UserId" = v."UserId"
);

-- ── Incident Photos ─────────────────────────────────────────
INSERT INTO "IncidentPhotos" ("IncidentId", "BlobUrl")
SELECT v."IncidentId", v."BlobUrl"
FROM (VALUES
  ('d4d4d4d4-0000-0000-0000-000000000001'::uuid, 'https://placeholder.saferoad.dev/photos/kepez-cukur-01a.jpg'),
  ('d4d4d4d4-0000-0000-0000-000000000001'::uuid, 'https://placeholder.saferoad.dev/photos/kepez-cukur-01b.jpg'),
  ('d4d4d4d4-0000-0000-0000-000000000002'::uuid, 'https://placeholder.saferoad.dev/photos/kepez-su-baskini-02.jpg'),
  ('d4d4d4d4-0000-0000-0000-000000000004'::uuid, 'https://placeholder.saferoad.dev/photos/kepez-kaza-04a.jpg'),
  ('d4d4d4d4-0000-0000-0000-000000000004'::uuid, 'https://placeholder.saferoad.dev/photos/kepez-kaza-04b.jpg'),
  ('d4d4d4d4-0000-0000-0000-000000000007'::uuid, 'https://placeholder.saferoad.dev/photos/muratpasa-cukur-07.jpg'),
  ('d4d4d4d4-0000-0000-0000-000000000008'::uuid, 'https://placeholder.saferoad.dev/photos/kaleici-su-08.jpg'),
  ('d4d4d4d4-0000-0000-0000-000000000009'::uuid, 'https://placeholder.saferoad.dev/photos/lara-kaza-09.jpg'),
  ('d4d4d4d4-0000-0000-0000-000000000013'::uuid, 'https://placeholder.saferoad.dev/photos/konyaalti-taskin-13a.jpg'),
  ('d4d4d4d4-0000-0000-0000-000000000013'::uuid, 'https://placeholder.saferoad.dev/photos/konyaalti-taskin-13b.jpg'),
  ('d4d4d4d4-0000-0000-0000-000000000015'::uuid, 'https://placeholder.saferoad.dev/photos/konyaalti-kaza-15.jpg'),
  ('d4d4d4d4-0000-0000-0000-000000000018'::uuid, 'https://placeholder.saferoad.dev/photos/dosemealti-cukur-18.jpg'),
  ('d4d4d4d4-0000-0000-0000-000000000019'::uuid, 'https://placeholder.saferoad.dev/photos/dosemealti-sel-19.jpg'),
  ('d4d4d4d4-0000-0000-0000-000000000020'::uuid, 'https://placeholder.saferoad.dev/photos/dosemealti-kaza-20.jpg')
) AS v("IncidentId", "BlobUrl")
WHERE NOT EXISTS (
  SELECT 1 FROM "IncidentPhotos" px
  WHERE px."IncidentId" = v."IncidentId" AND px."BlobUrl" = v."BlobUrl"
);

-- ── Comments ────────────────────────────────────────────────
INSERT INTO "Comments" ("IncidentId", "UserId", "Content", "CreatedAt")
SELECT v."IncidentId", v."UserId", v."Content", v."CreatedAt"::timestamptz
FROM (VALUES
  ('d4d4d4d4-0000-0000-0000-000000000001'::uuid, 'c3c3c3c3-0000-0000-0000-000000000002'::uuid,
   'Bu çukur gerçekten çok tehlikeli, dün gece arabamın lastiği patladı!', '2026-02-15T15:00:00Z'),
  ('d4d4d4d4-0000-0000-0000-000000000001'::uuid, 'c3c3c3c3-0000-0000-0000-000000000003'::uuid,
   'Belediyeye bildirdim, 1 hafta içinde düzelteceklerini söylediler.', '2026-02-16T10:00:00Z'),
  ('d4d4d4d4-0000-0000-0000-000000000002'::uuid, 'c3c3c3c3-0000-0000-0000-000000000001'::uuid,
   'Her yağmurda aynı sorun, altyapı yetersiz.', '2026-02-19T08:00:00Z'),
  ('d4d4d4d4-0000-0000-0000-000000000004'::uuid, 'c3c3c3c3-0000-0000-0000-000000000002'::uuid,
   'Kaza bölgesi temizlendi ama yol çizgileri silinmiş.', '2026-02-23T09:00:00Z'),
  ('d4d4d4d4-0000-0000-0000-000000000007'::uuid, 'c3c3c3c3-0000-0000-0000-000000000001'::uuid,
   'Atatürk Bulvarı her kış aynı durum, kalıcı çözüm lazım.', '2026-02-17T10:00:00Z'),
  ('d4d4d4d4-0000-0000-0000-000000000008'::uuid, 'a1a1a1a1-0000-0000-0000-000000000004'::uuid,
   'Tarihi dokuya zarar vermeden drenaj sistemi kurulmalı.', '2026-02-20T09:00:00Z'),
  ('d4d4d4d4-0000-0000-0000-000000000013'::uuid, 'c3c3c3c3-0000-0000-0000-000000000003'::uuid,
   'Sahil yolunda dalga duvarı yapılması gerekiyor.', '2026-02-18T10:00:00Z'),
  ('d4d4d4d4-0000-0000-0000-000000000015'::uuid, 'c3c3c3c3-0000-0000-0000-000000000001'::uuid,
   'Çok tehlikeli bir kavşak, sinyalizasyon sorunu var.', '2026-02-21T08:00:00Z'),
  ('d4d4d4d4-0000-0000-0000-000000000018'::uuid, 'c3c3c3c3-0000-0000-0000-000000000001'::uuid,
   'TIR trafiği yüzünden yollar çok hızlı bozuluyor.', '2026-02-15T09:00:00Z'),
  ('d4d4d4d4-0000-0000-0000-000000000019'::uuid, 'a1a1a1a1-0000-0000-0000-000000000003'::uuid,
   'Dere yatağı temizlenmeli, her yıl aynı sel taşkını yaşanıyor.', '2026-03-01T12:00:00Z'),
  ('d4d4d4d4-0000-0000-0000-000000000021'::uuid, 'c3c3c3c3-0000-0000-0000-000000000001'::uuid,
   'Toprak kayması bölgesi işaretlenmeli, gece çok tehlikeli.', '2026-03-03T08:00:00Z'),
  ('d4d4d4d4-0000-0000-0000-000000000022'::uuid, 'c3c3c3c3-0000-0000-0000-000000000002'::uuid,
   'İnşaat devam ediyor, kaldırımlar bitince düzelecek.', '2026-01-22T14:00:00Z')
) AS v("IncidentId", "UserId", "Content", "CreatedAt")
WHERE NOT EXISTS (
  SELECT 1 FROM "Comments" cx
  WHERE cx."IncidentId" = v."IncidentId" AND cx."UserId" = v."UserId" AND cx."Content" = v."Content"
);

-- ── Summary ─────────────────────────────────────────────────
-- 3 new users, 22 incidents, 32 verifications, 14 photos, 12 comments
-- Municipalities: Kepez (6), Muratpaşa (6), Konyaaltı (5), Döşemealtı (5)
-- Categories: Pothole (6), Flooding (4), Road Accident (4), Obstacle (4), Damaged Sidewalk (4)
-- Status: Pending (6), Verified (6), Disputed (4), Resolved (4+2 existing = 6)
