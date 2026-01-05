-- ========================================
-- STEP 1: CREATE DATABASE
-- ========================================
CREATE DATABASE IF NOT EXISTS healthcare_appointment_system
CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;

USE healthcare_appointment_system;

-- ========================================
-- STEP 2: CREATE DOCTORS TABLE
-- ========================================
CREATE TABLE IF NOT EXISTS doctors (
    doctor_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    specialization VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL COLLATE utf8mb4_general_ci,
    phone VARCHAR(20),
    years_of_experience INT CHECK (years_of_experience >= 0),
    consultation_fee DECIMAL(10,2) CHECK (consultation_fee >= 0),
    rating DECIMAL(3,2) DEFAULT 0.00 CHECK (rating BETWEEN 0 AND 5),
    is_available BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ========================================
-- STEP 3: CREATE PATIENTS TABLE
-- ========================================
CREATE TABLE IF NOT EXISTS patients (
    patient_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL COLLATE utf8mb4_general_ci,
    phone VARCHAR(20) NOT NULL,
    date_of_birth DATE,
    gender ENUM('Male', 'Female', 'Other') NOT NULL,
    blood_group VARCHAR(5),
    address TEXT,
    medical_history TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ========================================
-- STEP 4: CREATE DOCTOR SCHEDULES TABLE
-- ========================================
CREATE TABLE IF NOT EXISTS doctor_schedules (
    schedule_id INT AUTO_INCREMENT PRIMARY KEY,
    doctor_id INT NOT NULL,
    day_of_week ENUM('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday') NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    slot_duration INT DEFAULT 30 CHECK (slot_duration > 0),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ========================================
-- STEP 5: CREATE APPOINTMENTS TABLE
-- ========================================
CREATE TABLE IF NOT EXISTS appointments (
    appointment_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    status ENUM('Scheduled','Confirmed','Cancelled','Completed','No-Show') DEFAULT 'Scheduled',
    reason_for_visit TEXT,
    symptoms TEXT,
    notes TEXT,
    cancellation_reason TEXT,
    cancelled_by ENUM('Patient','Doctor','System'),
    cancelled_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_appointment (doctor_id, appointment_date, appointment_time),
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ========================================
-- STEP 6: CREATE APPOINTMENT HISTORY TABLE
-- ========================================
CREATE TABLE IF NOT EXISTS appointment_history (
    history_id INT AUTO_INCREMENT PRIMARY KEY,
    appointment_id INT NOT NULL,
    changed_by VARCHAR(100),
    change_type ENUM('Created','Updated','Cancelled','Completed') NOT NULL,
    old_status VARCHAR(50),
    new_status VARCHAR(50),
    change_details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ========================================
-- STEP 7: CREATE CONVERSATION LOGS TABLE
-- ========================================
CREATE TABLE IF NOT EXISTS conversation_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT,
    conversation_type ENUM('Text','Voice') NOT NULL,
    user_message TEXT,
    bot_response TEXT,
    intent VARCHAR(100),
    entities JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ========================================
-- STEP 8: INSERT SAMPLE DATA (DOCTORS)
-- ========================================
INSERT INTO doctors (first_name, last_name, specialization, email, phone, years_of_experience, consultation_fee, rating)
VALUES
('Sarah', 'Johnson', 'Cardiologist', 'sarah.johnson@healthcare.com', '+92-300-1234567', 15, 3000.00, 4.8),
('Michael', 'Chen', 'Pediatrician', 'michael.chen@healthcare.com', '+92-300-2345678', 10, 2500.00, 4.9),
('Emily', 'Williams', 'Dermatologist', 'emily.williams@healthcare.com', '+92-300-3456789', 8, 2000.00, 4.7),
('David', 'Brown', 'Orthopedic Surgeon', 'david.brown@healthcare.com', '+92-300-4567890', 12, 3500.00, 4.6),
('Jennifer', 'Davis', 'General Physician', 'jennifer.davis@healthcare.com', '+92-300-5678901', 7, 1500.00, 4.5),
('Robert', 'Miller', 'Neurologist', 'robert.miller@healthcare.com', '+92-300-6789012', 18, 4000.00, 4.9),
('Lisa', 'Wilson', 'Gynecologist', 'lisa.wilson@healthcare.com', '+92-300-7890123', 14, 2800.00, 4.8),
('James', 'Moore', 'Dentist', 'james.moore@healthcare.com', '+92-300-8901234', 9, 2200.00, 4.6),
('Maria', 'Taylor', 'Psychiatrist', 'maria.taylor@healthcare.com', '+92-300-9012345', 11, 3200.00, 4.7),
('Ahmed', 'Khan', 'ENT Specialist', 'ahmed.khan@healthcare.com', '+92-300-0123456', 13, 2600.00, 4.8);
ON DUPLICATE KEY UPDATE
  first_name = VALUES(first_name),
  last_name = VALUES(last_name),
  specialization = VALUES(specialization),
  phone = VALUES(phone),
  years_of_experience = VALUES(years_of_experience),
  consultation_fee = VALUES(consultation_fee),
  rating = VALUES(rating);

-- ========================================
-- STEP 9: INSERT SAMPLE PATIENTS
-- ========================================
INSERT INTO patients (first_name, last_name, email, phone, date_of_birth, gender, blood_group, address, medical_history)
VALUES
('Ali','Ahmad','ali.ahmad@email.com','+92-301-1111111','1990-05-15','Male','A+','House 123, Hayatabad, Peshawar','No major medical history'),
('Fatima','Hassan','fatima.hassan@email.com','+92-301-2222222','1985-08-22','Female','B+','Flat 45, University Town, Peshawar','Diabetes Type 2'),
('Usman','Malik','usman.malik@email.com','+92-301-3333333','1995-03-10','Male','O+','Street 7, Saddar, Peshawar','Asthma'),
('Ayesha','Raza','ayesha.raza@email.com','+92-301-4444444','1988-11-30','Female','AB+','Block C, Phase 3, Peshawar','Hypertension'),
('Bilal','Shah','bilal.shah@email.com','+92-301-5555555','1992-07-18','Male','A-','House 67, Cantt, Peshawar','No major medical history'),
('Zainab','Ali','zainab.ali@email.com','+92-301-6666666','1993-12-05','Female','O-','Apartment 22, Gulberg, Peshawar','Allergies to penicillin'),
('Hamza','Iqbal','hamza.iqbal@email.com','+92-301-7777777','1987-04-25','Male','B-','House 89, Warsak Road, Peshawar','Previous heart surgery'),
('Sara','Yousaf','sara.yousaf@email.com','+92-301-8888888','1991-09-14','Female','A+','Street 12, Regi, Peshawar','Migraine'),
('Imran','Durrani','imran.durrani@email.com','+92-301-9999999','1989-06-08','Male','O+','House 34, Jamrud Road, Peshawar','No major medical history'),
('Hina','Baig','hina.baig@email.com','+92-301-0000000','1994-02-20','Female','AB-','Flat 78, GT Road, Peshawar','Thyroid disorder');

-- ========================================
-- STEP 10: INSERT SAMPLE DOCTOR SCHEDULES
-- ========================================
INSERT INTO doctor_schedules (doctor_id, day_of_week, start_time, end_time, slot_duration) VALUES
(1,'Monday','09:00:00','17:00:00',30),
(1,'Wednesday','09:00:00','17:00:00',30),
(1,'Friday','09:00:00','17:00:00',30),
(2,'Tuesday','08:00:00','16:00:00',30),
(2,'Thursday','08:00:00','16:00:00',30),
(2,'Saturday','08:00:00','14:00:00',30),
(3,'Monday','10:00:00','18:00:00',45),
(3,'Tuesday','10:00:00','18:00:00',45),
(3,'Wednesday','10:00:00','18:00:00',45),
(3,'Thursday','10:00:00','18:00:00',45),
(4,'Monday','08:00:00','16:00:00',30),
(4,'Wednesday','08:00:00','16:00:00',30),
(4,'Friday','08:00:00','16:00:00',30),
(5,'Monday','09:00:00','17:00:00',20),
(5,'Tuesday','09:00:00','17:00:00',20),
(5,'Wednesday','09:00:00','17:00:00',20),
(5,'Thursday','09:00:00','17:00:00',20),
(5,'Friday','09:00:00','17:00:00',20),
(5,'Saturday','09:00:00','13:00:00',20),
(6,'Tuesday','10:00:00','18:00:00',40),
(6,'Thursday','10:00:00','18:00:00',40),
(7,'Monday','09:00:00','17:00:00',30),
(7,'Wednesday','09:00:00','17:00:00',30),
(7,'Friday','09:00:00','17:00:00',30),
(8,'Monday','08:00:00','16:00:00',30),
(8,'Tuesday','08:00:00','16:00:00',30),
(8,'Wednesday','08:00:00','16:00:00',30),
(8,'Thursday','08:00:00','16:00:00',30),
(8,'Friday','08:00:00','16:00:00',30),
(9,'Wednesday','10:00:00','18:00:00',60),
(9,'Thursday','10:00:00','18:00:00',60),
(9,'Friday','10:00:00','18:00:00',60),
(10,'Tuesday','09:00:00','17:00:00',30),
(10,'Thursday','09:00:00','17:00:00',30),
(10,'Saturday','09:00:00','13:00:00',30);

-- ========================================
-- STEP 11: INSERT SAMPLE APPOINTMENTS
-- ========================================
INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, status, reason_for_visit, symptoms)
VALUES
(1,1,'2025-10-22','10:00:00','Scheduled','Chest pain checkup','Chest pain, shortness of breath'),
(2,5,'2025-10-21','11:00:00','Confirmed','Diabetes follow-up','Regular checkup'),
(3,2,'2025-10-23','09:00:00','Scheduled','Child vaccination','Routine vaccination'),
(4,1,'2025-10-22','14:00:00','Scheduled','Blood pressure monitoring','High BP readings'),
(5,8,'2025-10-21','10:00:00','Confirmed','Dental cleaning','Routine cleaning'),
(6,3,'2025-10-24','15:00:00','Scheduled','Skin rash','Itchy rash on arms'),
(7,4,'2025-10-22','11:00:00','Scheduled','Knee pain','Pain in left knee'),
(8,9,'2025-10-24','11:00:00','Scheduled','Anxiety consultation','Stress and anxiety'),
(9,5,'2025-10-21','14:00:00','Confirmed','General checkup','Annual physical'),
(10,10,'2025-10-23','10:00:00','Scheduled','Ear infection','Pain in right ear');

-- ========================================
-- STEP 12: CREATE INDEXES
-- ========================================
CREATE INDEX idx_doctor_specialization ON doctors(specialization);
CREATE INDEX idx_doctor_availability ON doctors(is_available);
CREATE INDEX idx_appointment_date ON appointments(appointment_date);
CREATE INDEX idx_appointment_status ON appointments(status);
CREATE INDEX idx_patient_email ON patients(email);
CREATE INDEX idx_patient_phone ON patients(phone);
CREATE INDEX idx_schedule_doctor ON doctor_schedules(doctor_id);

-- ========================================
-- STEP 13: CREATE VIEWS
-- ========================================
CREATE OR REPLACE VIEW v_upcoming_appointments AS
SELECT 
    a.appointment_id,
    CONCAT(p.first_name, ' ', p.last_name) AS patient_name,
    p.phone AS patient_phone,
    CONCAT(d.first_name, ' ', d.last_name) AS doctor_name,
    d.specialization,
    a.appointment_date,
    a.appointment_time,
    a.status,
    a.reason_for_visit
FROM appointments a
JOIN patients p ON a.patient_id = p.patient_id
JOIN doctors d ON a.doctor_id = d.doctor_id
WHERE a.appointment_date >= CURDATE()
AND a.status IN ('Scheduled','Confirmed')
ORDER BY a.appointment_date, a.appointment_time;

CREATE OR REPLACE VIEW v_doctor_availability AS
SELECT 
    d.doctor_id,
    CONCAT(d.first_name,' ',d.last_name) AS doctor_name,
    d.specialization,
    d.email,
    d.phone,
    d.consultation_fee,
    d.rating,
    ds.day_of_week,
    ds.start_time,
    ds.end_time,
    ds.slot_duration
FROM doctors d
JOIN doctor_schedules ds ON d.doctor_id = ds.doctor_id
WHERE d.is_available = TRUE AND ds.is_active = TRUE
ORDER BY d.specialization, d.doctor_id, ds.day_of_week;

-- ========================================
-- STEP 14: SUCCESS MESSAGE
-- ========================================
SELECT '✅ Healthcare Appointment System Database setup completed successfully!' AS Status;
