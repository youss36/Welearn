CREATE DATABASE IF NOT EXISTS welearn_crm
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE welearn_crm;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS commissions;
DROP TABLE IF EXISTS lead_documents;
DROP TABLE IF EXISTS lead_status_history;
DROP TABLE IF EXISTS leads;
DROP TABLE IF EXISTS universities;
DROP TABLE IF EXISTS influencers;
DROP TABLE IF EXISTS users;
SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  email VARCHAR(160) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL,
  role ENUM('admin', 'conseiller') NOT NULL DEFAULT 'conseiller',
  public_token VARCHAR(64),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE influencers (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  email VARCHAR(160) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL,
  promo_code VARCHAR(80) NOT NULL UNIQUE,
  commission_rate DECIMAL(5,2) NOT NULL DEFAULT 0.00,
  public_token VARCHAR(64),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE universities (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  city VARCHAR(120) NOT NULL,
  country ENUM('Allemagne', 'Turquie', 'Hongrie', 'Espagne', 'Chine', 'Malte', 'Autre') NOT NULL,
  website VARCHAR(255),
  available_programs TEXT,
  study_domain VARCHAR(160),
  degree_level VARCHAR(120),
  teaching_language VARCHAR(120),
  tuition_fee DECIMAL(10,2) DEFAULT 0,
  scholarships_available BOOLEAN NOT NULL DEFAULT FALSE,
  without_language_certificate BOOLEAN NOT NULL DEFAULT FALSE,
  guaranteed_admission BOOLEAN NOT NULL DEFAULT FALSE,
  admission_conditions TEXT,
  required_documents TEXT,
  deadlines VARCHAR(160),
  internal_notes TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE leads (
  id INT AUTO_INCREMENT PRIMARY KEY,
  full_name VARCHAR(160) NOT NULL,
  phone VARCHAR(60),
  whatsapp VARCHAR(60),
  email VARCHAR(160),
  study_level VARCHAR(120),
  average_score VARCHAR(60),
  budget DECIMAL(10,2),
  desired_destination VARCHAR(120),
  speciality VARCHAR(160),
  source VARCHAR(120),
  assigned_conseiller_id INT,
  influencer_id INT,
  agent_id INT,
  status ENUM(
    'Nouveau lead',
    'Contacte',
    'Interesse',
    'Documents demandes',
    'Documents recus',
    'Universite selectionnee',
    'Candidature deposee',
    'Admission obtenue',
    'Paiement effectue',
    'Visa en cours',
    'Visa obtenu',
    'Depart confirme',
    'Dossier cloture'
  ) NOT NULL DEFAULT 'Nouveau lead',
  estimated_revenue DECIMAL(10,2) DEFAULT 0,
  internal_notes TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (assigned_conseiller_id) REFERENCES users(id) ON DELETE SET NULL,
  FOREIGN KEY (influencer_id) REFERENCES influencers(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE lead_status_history (
  id INT AUTO_INCREMENT PRIMARY KEY,
  lead_id INT NOT NULL,
  old_status VARCHAR(80),
  new_status VARCHAR(80) NOT NULL,
  changed_by_user_id INT,
  note TEXT,
  changed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE,
  FOREIGN KEY (changed_by_user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE lead_documents (
  id INT AUTO_INCREMENT PRIMARY KEY,
  lead_id INT NOT NULL,
  document_type ENUM('Passeport', 'Diplome', 'Releve de notes', 'CV', 'Lettre de motivation', 'Certificat de langue', 'Autre') NOT NULL,
  file_name VARCHAR(255) NOT NULL,
  file_path VARCHAR(500) NOT NULL,
  uploaded_by_user_id INT,
  uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE,
  FOREIGN KEY (uploaded_by_user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE commissions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  influencer_id INT NOT NULL,
  lead_id INT,
  status ENUM('estimee', 'validee', 'payee') NOT NULL DEFAULT 'estimee',
  amount DECIMAL(10,2) NOT NULL DEFAULT 0,
  payment_note TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  paid_at TIMESTAMP NULL,
  FOREIGN KEY (influencer_id) REFERENCES influencers(id) ON DELETE CASCADE,
  FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE appointments (
  id INT AUTO_INCREMENT PRIMARY KEY,
  lead_id INT NOT NULL,
  title VARCHAR(255) NOT NULL DEFAULT 'Rendez-vous',
  appointment_date DATE NOT NULL,
  appointment_time TIME NOT NULL,
  duration_minutes INT NOT NULL DEFAULT 60,
  location VARCHAR(255),
  type ENUM('présentiel','appel','visio','autre') NOT NULL DEFAULT 'présentiel',
  status ENUM('prévu','confirmé','annulé','réalisé') NOT NULL DEFAULT 'prévu',
  notes TEXT,
  created_by INT,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE,
  FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO users (name, email, password, role) VALUES
('Admin We Learn', 'admin@welearn.com', 'admin123', 'admin'),
('Sonia Conseillere', 'sonia@welearn.com', 'sonia123', 'conseiller');

INSERT INTO influencers (name, email, password, promo_code, commission_rate) VALUES
('Influenceur Demo', 'influencer@welearn.com', 'inf123', 'influenceur001', 10.00);

INSERT INTO universities (
  name, city, country, website, available_programs, study_domain, degree_level,
  teaching_language, tuition_fee, scholarships_available,
  without_language_certificate, guaranteed_admission, admission_conditions,
  required_documents, deadlines, internal_notes
) VALUES
(
  'Technical University of Munich (TUM)', 'Munich', 'Allemagne', 'https://www.tum.de',
  'Software Engineering, Robotics, Biomedical Engineering, MBA',
  'Informatique et Ingenierie', 'Master, MBA, Doctorat', 'Anglais / Allemand',
  0, TRUE, FALSE, FALSE,
  'Excellent dossier academique, TOEFL iBT 88 ou IELTS 6.5 selon le programme.',
  'Diplome, releves de notes, certificat de langue, CV, lettres de recommandation.',
  '31 Mai 2026', 'Universite tres demandee. Verifier les frais administratifs par semestre.'
),
(
  'Istanbul Technical University', 'Istanbul', 'Turquie', 'https://www.itu.edu.tr',
  'Engineering, Architecture, Computer Science, Management',
  'Ingenierie', 'Licence, Master', 'Anglais / Turc',
  2500, TRUE, FALSE, TRUE,
  'Dossier academique complet. Certains programmes demandent un test de langue.',
  'Passeport, diplome, releves, photo, formulaire de candidature.',
  '15 Juillet 2026', 'Bonne option pour budget moyen et admission rapide.'
),
(
  'University of Szeged', 'Szeged', 'Hongrie', 'https://u-szeged.hu',
  'Medicine, Business, Computer Science, Humanities',
  'Medecine et Business', 'Licence, Master, Doctorat', 'Anglais',
  4200, TRUE, TRUE, FALSE,
  'Entretien possible selon le programme. Niveau anglais recommande.',
  'Passeport, releves, diplome, CV, lettre de motivation.',
  '30 Juin 2026', 'Verifier les programmes de medecine separement.'
);

INSERT INTO leads (
  full_name, phone, whatsapp, email, study_level, average_score, budget,
  desired_destination, speciality, source, assigned_conseiller_id,
  influencer_id, status, estimated_revenue, internal_notes
) VALUES
(
  'Ahmed Ben Ali', '+216 51 000 000', '+216 51 000 000', 'ahmed@example.com',
  'Licence', '14/20', 4500, 'Allemagne', 'Informatique', 'Formulaire web',
  2, 1, 'Nouveau lead', 1200, 'Profil interesse par les programmes en anglais.'
);

INSERT INTO lead_status_history (lead_id, old_status, new_status, changed_by_user_id, note) VALUES
(1, NULL, 'Nouveau lead', 2, 'Lead cree depuis les donnees demo.');
