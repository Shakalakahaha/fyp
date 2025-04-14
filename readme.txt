# Flask Web Application

A simple web application built with Flask. (Churn Buster)

ok let me explain u my project
i have done the authentication part
let me explain u, 
1 company can have only 1 developer but many user
which dev and user need to register for company to get the company id, they will use this company id to register their acc

the part that i havent done

there are 5 trained models in the models/default_models/, which i used to train in local orange and import to my project for prediction usage
which include the pkl (for prediction) and their correspond metadata.pkl (for retrieve performance metrics)
1. initialization
this system will initialize the following for the developer and user, since the default model are the same for all of them
for developer: 5 default model pkl (for predictions) + 5 default model metadata.pkl (for retrieve metrics) + 1 ori dataset
for user: 5 default model pkl (for predictions)
since they are common, so it will store the all the 5 models in the model table (and also the metrics), and the ori dataset in dataset table

the following shows the format of the metadata.pkl
{
    'model_type': 'Neural Network',
    'metrics': {
        'Accuracy': 0.8096348096348096,  # Note: Capital 'A'
        'AUC': 0.850327660103112,        # Note: 'AUC' instead of 'roc_auc'
        'Precision': 0.8008413413551754,  # Note: Capital 'P'
        'Recall': 0.8096348096348096,    # Note: Capital 'R'
        'F1 Score': 0.8027330375218171   # Note: 'F1 Score' instead of 'f1_score'
    }
}

what dev do
they can retrain only the model with the highest accuracy within the default model which is neural network
1. by upload their dataset
2. system will combine the upload dataset with the initialize dataset for the first time retrain
it will store like this in the database in the dataset table
uploadDataset1
combinedDataset1
when second retrain, since the system will always retrieve the latest row from dataset table, then it will combine the upload dataset with the combinedDataset1
it will store like this
uploadDataset2
combinedDataset2

it will store like this in the server side
it will store the uploadDataset1 in the datasets/dev/uploadToRetrain/
and store the combinedDataset1 in the datasets/dev/combinedDataset/

3. then system will retrain the neural network model based on the combined dataset everytime with the default parameter 
the default parameter are as follows:
{
    neurons in hidden layer: 100, 50
    activation: identity
    solver: sgd
    regularization, alpha: 0.1
    maximal number of iterations: 200
    checked replicable training
}
and the system will train and evaluate the model on 80/20 split of the combined dataset

once the retrain is done, system will shows the training result with metrics and store in database. for naming convention, it will start with (v2, v3, ...). and there will be a model manager, that include the 5 default model + the number of version for neural network model. dev can choose to deploy the version to user based on their decision, when they choose to deploy, the user selection of model to predict will (5 default model +1, +2, ... based on how many version have deploy by dev)
and the output of the retrain model will allow user to use that retrain model pkl to predict that will store in server side models/retrained_models/

4. they can also do prediction

what user do 
they can do prediction
for user that dont have developer tracked in the database, they will use the 5 default model provide by system to made prediction
for user that have developer tracked in the database, once their dev have deploy a new version of neural network model, then their selection of model to predict will also (5 default model +1, +2, ... based on how many version have deploy by dev)
the flow will be like, 
1. create a prediction name
2. choose model
3. start predict
4. store prediction result (for history used)

it will store like this in the server side
for dev prediction,
it will store uploadDataset in datasets/dev/uploadToPredict/
and store the prediction result in datasets/dev/predictionResult/

for user prediction,
it will store uploadDataset in datasets/user/uploadToPredict/
and store the prediction result in datasets/user/predictionResult/

since dev and user are using the same predict churn function, they will have different frontend but with a shared backend with (different session id implement)

the following shows the defined database structure
-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Apr 12, 2025 at 10:09 AM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `fyp_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `companies`
--

CREATE TABLE `companies` (
  `id` varchar(10) NOT NULL,
  `name` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  `registration_date` datetime DEFAULT current_timestamp(),
  `email_verified` tinyint(1) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `datasets`
--

CREATE TABLE `datasets` (
  `id` int(11) NOT NULL,
  `company_id` varchar(10) DEFAULT NULL,
  `name` varchar(255) NOT NULL,
  `file_path` varchar(255) NOT NULL,
  `is_original` tinyint(1) DEFAULT NULL,
  `is_uploaded` tinyint(1) DEFAULT NULL,
  `is_combined` tinyint(1) DEFAULT NULL,
  `parent_dataset_id` int(11) DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `developers`
--

CREATE TABLE `developers` (
  `id` int(11) NOT NULL,
  `company_id` varchar(10) NOT NULL,
  `email` varchar(255) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `registration_date` datetime DEFAULT current_timestamp(),
  `email_verified` tinyint(1) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `modeldeployments`
--

CREATE TABLE `modeldeployments` (
  `id` int(11) NOT NULL,
  `company_id` varchar(10) NOT NULL,
  `model_id` int(11) NOT NULL,
  `deployed_by` int(11) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT NULL,
  `deployed_at` datetime DEFAULT current_timestamp(),
  `deactivated_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `modelmetrics`
--

CREATE TABLE `modelmetrics` (
  `id` int(11) NOT NULL,
  `model_id` int(11) NOT NULL,
  `accuracy` float DEFAULT NULL,
  `precision` float DEFAULT NULL,
  `recall` float DEFAULT NULL,
  `f1_score` float DEFAULT NULL,
  `auc_roc` float DEFAULT NULL,
  `additional_metrics` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`additional_metrics`)),
  `created_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `models`
--

CREATE TABLE `models` (
  `id` int(11) NOT NULL,
  `model_type_id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `version` varchar(10) NOT NULL,
  `file_path` varchar(255) NOT NULL,
  `is_default` tinyint(1) DEFAULT NULL,
  `company_id` varchar(10) DEFAULT NULL,
  `training_dataset_id` int(11) DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `modeltypes`
--

CREATE TABLE `modeltypes` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `description` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `predictions`
--

CREATE TABLE `predictions` (
  `id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `developer_id` int(11) DEFAULT NULL,
  `model_id` int(11) NOT NULL,
  `prediction_name` varchar(255) NOT NULL,
  `input_data` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`input_data`)),
  `result` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`result`)),
  `upload_dataset_path` varchar(255) DEFAULT NULL,
  `result_dataset_path` varchar(255) DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `company_id` varchar(10) NOT NULL,
  `email` varchar(255) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `registration_date` datetime DEFAULT current_timestamp(),
  `email_verified` tinyint(1) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `companies`
--
ALTER TABLE `companies`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- Indexes for table `datasets`
--
ALTER TABLE `datasets`
  ADD PRIMARY KEY (`id`),
  ADD KEY `company_id` (`company_id`),
  ADD KEY `parent_dataset_id` (`parent_dataset_id`);

--
-- Indexes for table `developers`
--
ALTER TABLE `developers`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_company_developer` (`company_id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- Indexes for table `modeldeployments`
--
ALTER TABLE `modeldeployments`
  ADD PRIMARY KEY (`id`),
  ADD KEY `company_id` (`company_id`),
  ADD KEY `model_id` (`model_id`),
  ADD KEY `deployed_by` (`deployed_by`);

--
-- Indexes for table `modelmetrics`
--
ALTER TABLE `modelmetrics`
  ADD PRIMARY KEY (`id`),
  ADD KEY `model_id` (`model_id`);

--
-- Indexes for table `models`
--
ALTER TABLE `models`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_model_version_company` (`model_type_id`,`version`,`company_id`),
  ADD KEY `company_id` (`company_id`),
  ADD KEY `training_dataset_id` (`training_dataset_id`);

--
-- Indexes for table `modeltypes`
--
ALTER TABLE `modeltypes`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`);

--
-- Indexes for table `predictions`
--
ALTER TABLE `predictions`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `developer_id` (`developer_id`),
  ADD KEY `model_id` (`model_id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`),
  ADD KEY `company_id` (`company_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `datasets`
--
ALTER TABLE `datasets`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=123;

--
-- AUTO_INCREMENT for table `developers`
--
ALTER TABLE `developers`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `modeldeployments`
--
ALTER TABLE `modeldeployments`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=22;

--
-- AUTO_INCREMENT for table `modelmetrics`
--
ALTER TABLE `modelmetrics`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=34;

--
-- AUTO_INCREMENT for table `models`
--
ALTER TABLE `models`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=38;

--
-- AUTO_INCREMENT for table `modeltypes`
--
ALTER TABLE `modeltypes`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT for table `predictions`
--
ALTER TABLE `predictions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=32;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `datasets`
--
ALTER TABLE `datasets`
  ADD CONSTRAINT `datasets_ibfk_1` FOREIGN KEY (`company_id`) REFERENCES `companies` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `datasets_ibfk_2` FOREIGN KEY (`parent_dataset_id`) REFERENCES `datasets` (`id`);

--
-- Constraints for table `developers`
--
ALTER TABLE `developers`
  ADD CONSTRAINT `developers_ibfk_1` FOREIGN KEY (`company_id`) REFERENCES `companies` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `modeldeployments`
--
ALTER TABLE `modeldeployments`
  ADD CONSTRAINT `modeldeployments_ibfk_1` FOREIGN KEY (`company_id`) REFERENCES `companies` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `modeldeployments_ibfk_2` FOREIGN KEY (`model_id`) REFERENCES `models` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `modeldeployments_ibfk_3` FOREIGN KEY (`deployed_by`) REFERENCES `developers` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `modelmetrics`
--
ALTER TABLE `modelmetrics`
  ADD CONSTRAINT `modelmetrics_ibfk_1` FOREIGN KEY (`model_id`) REFERENCES `models` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `models`
--
ALTER TABLE `models`
  ADD CONSTRAINT `models_ibfk_1` FOREIGN KEY (`model_type_id`) REFERENCES `modeltypes` (`id`),
  ADD CONSTRAINT `models_ibfk_2` FOREIGN KEY (`company_id`) REFERENCES `companies` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `models_ibfk_3` FOREIGN KEY (`training_dataset_id`) REFERENCES `datasets` (`id`);

--
-- Constraints for table `predictions`
--
ALTER TABLE `predictions`
  ADD CONSTRAINT `predictions_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `predictions_ibfk_2` FOREIGN KEY (`developer_id`) REFERENCES `developers` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `predictions_ibfk_3` FOREIGN KEY (`model_id`) REFERENCES `models` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `users`
--
ALTER TABLE `users`
  ADD CONSTRAINT `users_ibfk_1` FOREIGN KEY (`company_id`) REFERENCES `companies` (`id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;