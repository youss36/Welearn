-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Hôte : 127.0.0.1:3307
-- Généré le : mer. 01 juil. 2026 à 02:38
-- Version du serveur : 10.4.32-MariaDB
-- Version de PHP : 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de données : `welearn_crm`
--

-- --------------------------------------------------------

--
-- Structure de la table `universities_detail`
--

CREATE TABLE `universities_detail` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `city` varchar(100) NOT NULL,
  `country` varchar(100) NOT NULL,
  `website` varchar(255) DEFAULT NULL,
  `available_programs` text DEFAULT NULL,
  `degree_level` varchar(100) DEFAULT NULL,
  `teaching_language` varchar(50) DEFAULT NULL,
  `tuition_fee` int(11) DEFAULT NULL,
  `scholarships_available` text DEFAULT NULL,
  `admission_conditions` text DEFAULT NULL,
  `required_documents` text DEFAULT NULL,
  `deadlines` varchar(100) DEFAULT NULL,
  `internal_notes` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `universities_detail`
--

INSERT INTO `universities_detail` (`id`, `name`, `city`, `country`, `website`, `available_programs`, `degree_level`, `teaching_language`, `tuition_fee`, `scholarships_available`, `admission_conditions`, `required_documents`, `deadlines`, `internal_notes`, `created_at`) VALUES
(1, 'Sorbonne Université', 'Paris', 'France', 'https://www.sorbonne-universite.fr', 'Informatique, Intelligence Artificielle, Data Science, Gestion', 'Licence, Master, Doctorat', 'Français', 450, 'Bourse Eiffel disponible pour les étudiants internationaux, Bourse du CROUS', 'Moyenne supérieure à 14/20, niveau de langue de B2 minimum en Français', 'Diplôme du Bac, Relevés de notes, Lettre de motivation, CV, Attestation TCF/DELF', '31 Mai 2026', 'Excellente université pour les profils académiques. Procédure Campus France obligatoire.', '2026-07-01 00:31:54'),
(2, 'Technical University of Munich (TUM)', 'Munich', 'Allemagne', 'https://www.tum.de', 'Software Engineering, Robotics, Biomedical Engineering, MBA', 'Master, MBA, Doctorat', 'Anglais / Allemand', 0, 'Bourses DAAD, Deutschlandstipendium pour les excellents profils', 'Test d\'admission écrit, TOEFL iBT score minimum 88 ou IELTS 6.5', 'Diplôme de Licence, Certificat de langue, Lettres de recommandation, Syllabus des cours', '31 Mai 2026', 'Frais de scolarité gratuits (uniquement frais administratifs de 150€). Très demandée.', '2026-07-01 00:31:54');

--
-- Index pour les tables déchargées
--

--
-- Index pour la table `universities_detail`
--
ALTER TABLE `universities_detail`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT pour les tables déchargées
--

--
-- AUTO_INCREMENT pour la table `universities_detail`
--
ALTER TABLE `universities_detail`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
