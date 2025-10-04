<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Course2Career - AI-Powered Learning Paths</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #10b981;
            --primary-dark: #059669;
            --primary-light: #d1fae5;
            --accent: #3b82f6;
            --accent-dark: #2563eb;
            --bg-primary: #ffffff;
            --bg-secondary: #f9fafb;
            --bg-tertiary: #f3f4f6;
            --text-primary: #111827;
            --text-secondary: #6b7280;
            --text-light: #9ca3af;
            --border: #e5e7eb;
            --danger: #ef4444;
            --success: #10b981;
            --warning: #f59e0b;
            --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
            --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
            --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
            --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1);
            --radius-sm: 0.375rem;
            --radius-md: 0.5rem;
            --radius-lg: 0.75rem;
            --radius-xl: 1rem;
        }
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-secondary);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        main {
            flex: 1;
        }
        .view-section {
            display: none;
        }
        .view-section.active {
            display: block;
        }
        header {
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border);
            position: sticky;
            top: 0;
            z-index: 1000;
            transition: all 0.3s ease;
        }
        header.scrolled {
            box-shadow: var(--shadow-md);
        }
        .header-content {
            max-width: 1280px;
            margin: 0 auto;
            padding: 1rem 1.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 2rem;
        }
        .logo {
            font-size: 1.5rem;
            font-weight: 900;
            background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-decoration: none;
            letter-spacing: -0.5px;
        }
        .nav-links {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .nav-links a {
            padding: 0.5rem 1rem;
            border-radius: var(--radius-md);
            font-weight: 500;
            font-size: 0.9rem;
            color: var(--text-secondary);
            text-decoration: none;
            transition: all 0.2s ease;
        }
        .nav-links a:hover {
            background: var(--bg-tertiary);
            color: var(--text-primary);
        }
        .nav-links a.active {
            background: var(--primary);
            color: white;
        }
        .nav-links .btn-primary {
            background: var(--primary);
            color: white;
        }
        .nav-links .btn-primary:hover {
            background: var(--primary-dark);
        }
        .mobile-menu-btn {
            display: none;
            background: none;
            border: none;
            cursor: pointer;
            padding: 0.5rem;
        }
        .mobile-menu-btn span {
            display: block;
            width: 24px;
            height: 2px;
            background: var(--text-primary);
            margin: 5px 0;
            transition: 0.3s;
        }
        .container {
            max-width: 1280px;
            margin: 0 auto;
            padding: 0 1.5rem;
        }
        .hero {
            padding: 6rem 1.5rem 4rem;
            text-align: center;
            background: linear-gradient(135deg, #f0fdf4 0%, #dbeafe 100%);
        }
        .hero h1 {
            font-size: clamp(2.5rem, 5vw, 4rem);
            font-weight: 900;
            line-height: 1.1;
            margin-bottom: 1.5rem;
            background: linear-gradient(135deg, var(--text-primary) 0%, var(--primary) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .hero p {
            font-size: clamp(1.1rem, 2vw, 1.3rem);
            color: var(--text-secondary);
            max-width: 700px;
            margin: 0 auto 2rem;
        }
        .hero-buttons {
            display: flex;
            gap: 1rem;
            justify-content: center;
            flex-wrap: wrap;
        }
        .btn {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.875rem 2rem;
            border-radius: var(--radius-lg);
            font-weight: 600;
            font-size: 1rem;
            text-decoration: none;
            border: none;
            cursor: pointer;
            transition: all 0.2s ease;
            white-space: nowrap;
        }
        .btn-primary {
            background: var(--primary);
            color: white;
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
        }
        .btn-primary:hover {
            background: var(--primary-dark);
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
        }
        .btn-secondary {
            background: white;
            color: var(--text-primary);
            border: 2px solid var(--border);
        }
        .btn-secondary:hover {
            border-color: var(--primary);
            color: var(--primary);
        }
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        .features {
            padding: 5rem 1.5rem;
        }
        .section-header {
            text-align: center;
            margin-bottom: 4rem;
        }
        .section-header h2 {
            font-size: clamp(2rem, 4vw, 3rem);
            font-weight: 800;
            margin-bottom: 1rem;
        }
        .section-header p {
            font-size: 1.1rem;
            color: var(--text-secondary);
            max-width: 600px;
            margin: 0 auto;
        }
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin-top: 3rem;
        }
        .feature-card {
            background: white;
            border-radius: var(--radius-xl);
            padding: 2rem;
            border: 1px solid var(--border);
            transition: all 0.3s ease;
        }
        .feature-card:hover {
            transform: translateY(-4px);
            box-shadow: var(--shadow-xl);
            border-color: var(--primary-light);
        }
        .feature-icon {
            width: 56px;
            height: 56px;
            border-radius: var(--radius-lg);
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 1.5rem;
            font-size: 1.5rem;
        }
        .feature-card:nth-child(1) .feature-icon {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
        }
        .feature-card:nth-child(2) .feature-icon {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            color: white;
        }
        .feature-card:nth-child(3) .feature-icon {
            background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
            color: white;
        }
        .feature-card h3 {
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 0.75rem;
        }
        .feature-card p {
            color: var(--text-secondary);
            line-height: 1.7;
        }
        .auth-wrapper {
            min-height: calc(100vh - 200px);
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 3rem 1.5rem;
        }
        .auth-card {
            background: white;
            border-radius: var(--radius-xl);
            padding: 3rem;
            width: 100%;
            max-width: 460px;
            box-shadow: var(--shadow-xl);
            border: 1px solid var(--border);
        }
        .auth-card h1 {
            font-size: 2rem;
            font-weight: 800;
            margin-bottom: 0.5rem;
        }
        .auth-card > p {
            color: var(--text-secondary);
            margin-bottom: 2rem;
        }
        .form-group {
            margin-bottom: 1.5rem;
        }
        .form-group label {
            display: block;
            font-weight: 600;
            font-size: 0.875rem;
            margin-bottom: 0.5rem;
            color: var(--text-primary);
        }
        .form-group input {
            width: 100%;
            padding: 0.875rem 1rem;
            border: 2px solid var(--border);
            border-radius: var(--radius-md);
            font-size: 1rem;
            transition: all 0.2s ease;
            background: var(--bg-secondary);
        }
        .form-group input:focus {
            outline: none;
            border-color: var(--primary);
            background: white;
            box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
        }
        .auth-footer {
            margin-top: 2rem;
            text-align: center;
            color: var(--text-secondary);
        }
        .content-section {
            padding: 4rem 1.5rem;
        }
        .content-box {
            background: white;
            border-radius: var(--radius-xl);
            padding: 2.5rem;
            border: 1px solid var(--border);
            box-shadow: var(--shadow-md);
        }
        #view-dashboard .content-box {
            background: linear-gradient(135deg, #f0fdf4, #eef2ff);
        }
        #view-dashboard .content-box h1,
        #view-career-path .content-box h1 {
            background: linear-gradient(135deg, var(--primary), var(--accent));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .content-box > p {
            color: var(--text-secondary);
            margin-bottom: 2rem;
        }
        .ai-form {
            display: flex;
            gap: 1rem;
            margin-top: 2rem;
        }
        .ai-form input {
            flex: 1;
            padding: 1rem 1.25rem;
            border: 2px solid var(--border);
            border-radius: var(--radius-lg);
            font-size: 1rem;
            transition: all 0.2s ease;
            background: white;
        }
        .ai-form input:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.2);
        }
        .ai-form button {
            padding: 1rem 2rem;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: var(--radius-lg);
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .ai-form button:hover {
            background: var(--primary-dark);
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }
        .loading {
            text-align: center;
            padding: 3rem;
            color: var(--text-secondary);
        }
        .spinner {
            display: inline-block;
            width: 40px;
            height: 40px;
            border: 4px solid var(--border);
            border-top-color: var(--primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            to {
                transform: rotate(360deg);
            }
        }
        .course-card {
            background: white;
            border-radius: var(--radius-xl);
            padding: 2.5rem;
            margin-top: 2rem;
            border: 1px solid var(--border);
            animation: slideUp 0.5s ease;
            box-shadow: var(--shadow-lg);
        }
        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        .course-header h3 {
            font-size: 2rem;
            font-weight: 800;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, var(--primary-dark), var(--accent-dark));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .course-header p {
            font-size: 1.1rem;
            color: var(--text-secondary);
            margin-bottom: 2rem;
        }
        .course-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1.5rem;
            padding: 1.5rem;
            background: var(--bg-secondary);
            border-radius: var(--radius-lg);
            margin: 2rem 0;
        }
        .stat-item {
            text-align: center;
        }
        .stat-label {
            display: block;
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--text-light);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.5rem;
        }
        .stat-value {
            display: block;
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--text-primary);
        }
        .skills-section,
        .modules-section {
            margin-top: 2rem;
        }
        .skills-section h4,
        .modules-section h4 {
            font-size: 1.25rem;
            font-weight: 700;
            margin-bottom: 1rem;
        }
        .skills-list {
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem;
            list-style: none;
        }
        .skill-tag {
            padding: 0.5rem 1rem;
            background: var(--primary-light);
            color: var(--primary-dark);
            border-radius: 99px;
            font-size: 0.875rem;
            font-weight: 600;
            border: 1px solid rgba(16, 185, 129, 0.2);
        }
        .module-list {
            display: grid;
            gap: 1rem;
        }
        .module-item {
            padding: 1.5rem;
            background: var(--bg-secondary);
            border-radius: var(--radius-lg);
            border: 1px solid var(--border);
            transition: all 0.2s ease;
        }
        .module-item:hover {
            border-color: var(--primary);
            box-shadow: var(--shadow-md);
            transform: translateY(-2px);
        }
        .module-item h5 {
            font-size: 1.1rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        .module-item p {
            color: var(--text-secondary);
        }
        .career-path-container {
            margin-top: 3rem;
        }
        .path-header {
            text-align: center;
            margin-bottom: 3rem;
        }
        .path-header h2 {
            font-size: 2.2rem;
            font-weight: 800;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, #1f2937, #4b5563);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .career-stages {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 2rem;
        }
        .career-stage {
            color: white;
            border-radius: var(--radius-xl);
            padding: 2rem;
            box-shadow: var(--shadow-lg);
            transition: all 0.3s ease;
        }
        .career-stage:hover {
            transform: translateY(-5px);
            box-shadow: var(--shadow-xl);
        }
        .career-stage.entry {
            background: linear-gradient(135deg, #84cc16, #4d7c0f);
        }
        .career-stage.mid {
            background: linear-gradient(135deg, #2563eb, #1e3a8a);
        }
        .career-stage.late {
            background: linear-gradient(135deg, #7c3aed, #4c1d95);
        }
        .stage-header {
            text-align: center;
            margin-bottom: 1.5rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.3);
            padding-bottom: 1rem;
        }
        .stage-header h3 {
            font-size: 1.5rem;
            font-weight: 700;
        }
        .role-card {
            padding: 1.25rem;
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: var(--radius-lg);
            margin-bottom: 1rem;
            text-align: center;
            transition: all 0.2s ease;
        }
        .role-card:hover {
            background: rgba(255, 255, 255, 0.2);
            transform: scale(1.03);
        }
        .role-title {
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        .role-salary {
            color: rgba(255, 255, 255, 0.9);
            font-size: 0.875rem;
        }
        .saved-layout {
            display: grid;
            grid-template-columns: 320px 1fr;
            gap: 2rem;
            align-items: start;
        }
        .saved-sidebar {
            background: white;
            border-radius: var(--radius-xl);
            padding: 1.5rem;
            border: 1px solid var(--border);
            position: sticky;
            top: 100px;
        }
        .saved-sidebar h3 {
            font-size: 1.25rem;
            font-weight: 700;
            margin-bottom: 1rem;
        }
        .saved-list {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }
        .saved-item {
            width: 100%;
            text-align: left;
            padding: 1rem;
            background: var(--bg-secondary);
            border: 2px solid transparent;
            border-radius: var(--radius-md);
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .saved-item:hover {
            background: var(--bg-tertiary);
        }
        .saved-item.active {
            background: var(--primary-light);
            color: var(--primary-dark);
            border-color: var(--primary);
            font-weight: 600;
        }
        .saved-display {
            min-height: 400px;
        }
        .admin-table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: var(--radius-xl);
            overflow: hidden;
            box-shadow: var(--shadow-md);
        }
        .admin-table th,
        .admin-table td {
            padding: 1rem 1.5rem;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }
        .admin-table th {
            background: var(--bg-secondary);
            font-weight: 700;
            font-size: 0.875rem;
            text-transform: uppercase;
            color: var(--text-secondary);
            letter-spacing: 0.5px;
        }
        .admin-table tr:not(:last-child) {
             border-bottom: 1px solid var(--border);
        }
        .admin-table tr:hover {
            background: var(--bg-tertiary);
        }
        .delete-btn {
            padding: 0.5rem 1rem;
            background: #fef2f2;
            color: var(--danger);
            border: 1px solid #fee2e2;
            border-radius: var(--radius-md);
            font-size: 0.875rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .delete-btn:hover {
            background: var(--danger);
            color: white;
        }
        .toast-container {
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            z-index: 10000;
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }
        .toast {
            padding: 1rem 1.5rem;
            border-radius: var(--radius-lg);
            color: white;
            font-weight: 600;
            box-shadow: var(--shadow-xl);
            animation: slideInRight 0.3s ease;
            min-width: 300px;
        }
        @keyframes slideInRight {
            from {
                opacity: 0;
                transform: translateX(100%);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        .toast.error {
            background: var(--danger);
        }
        .toast.success {
            background: var(--success);
        }
        .modal-overlay {
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.5);
            backdrop-filter: blur(4px);
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s ease;
        }
        .modal-overlay.active {
            opacity: 1;
            pointer-events: auto;
        }
        .modal-content {
            background: white;
            border-radius: var(--radius-xl);
            padding: 2rem;
            max-width: 480px;
            width: 90%;
            box-shadow: var(--shadow-xl);
            transform: scale(0.9);
            transition: transform 0.3s ease;
        }
        .modal-overlay.active .modal-content {
            transform: scale(1);
        }
        .modal-header {
            margin-bottom: 1rem;
        }
        .modal-header h3 {
            font-size: 1.5rem;
            font-weight: 700;
        }
        .modal-actions {
            display: flex;
            gap: 1rem;
            margin-top: 2rem;
            justify-content: flex-end;
        }
        .modal-actions button {
            flex-grow: 0;
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: var(--radius-md);
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .modal-actions .cancel {
            background: var(--bg-tertiary);
            color: var(--text-primary);
        }
        .modal-actions .confirm {
            background: var(--danger);
            color: white;
        }
        footer {
            background: white;
            border-top: 1px solid var(--border);
            padding: 3rem 1.5rem;
            margin-top: 5rem;
        }
        .footer-content {
            max-width: 1280px;
            margin: 0 auto;
            text-align: center;
        }
        .footer-content p {
            color: var(--text-secondary);
        }
        @media (max-width: 768px) {
            .mobile-menu-btn {
                display: block;
            }
            .nav-links {
                position: absolute;
                top: 100%;
                left: 0;
                right: 0;
                background: white;
                flex-direction: column;
                padding: 1rem;
                border-bottom: 1px solid var(--border);
                box-shadow: var(--shadow-lg);
                transform: translateY(-100%);
                opacity: 0;
                pointer-events: none;
                transition: all 0.3s ease;
            }
            .nav-links.active {
                transform: translateY(0);
                opacity: 1;
                pointer-events: auto;
            }
            .nav-links a {
                width: 100%;
                text-align: center;
                padding: 1rem;
            }
            .hero {
                padding: 4rem 1.5rem 3rem;
            }
            .hero-buttons {
                flex-direction: column;
            }
            .hero-buttons .btn {
                width: 100%;
                justify-content: center;
            }
            .feature-grid {
                grid-template-columns: 1fr;
            }
            .ai-form {
                flex-direction: column;
            }
            .course-stats {
                grid-template-columns: 1fr 1fr;
            }
            .career-stages {
                grid-template-columns: 1fr;
            }
            .saved-layout {
                grid-template-columns: 1fr;
            }
            .saved-sidebar {
                position: static;
            }
            .auth-card {
                padding: 2rem;
            }
            .toast-container {
                left: 1rem;
                right: 1rem;
                bottom: 1rem;
            }
            .toast {
                min-width: auto;
            }
        }
        @media (max-width: 480px) {
            .content-box {
                padding: 1.5rem;
            }
            .course-card {
                padding: 1.5rem;
            }
            .course-stats {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div id="toast-container" class="toast-container"></div>
    <div id="modal" class="modal-overlay">
        <div class="modal-content">
            <div class="modal-header">
                <h3 id="modal-title">Are you sure?</h3>
                <p id="modal-message">This action cannot be undone.</p>
            </div>
            <div class="modal-actions">
                <button class="cancel" id="modal-cancel">Cancel</button>
                <button class="confirm" id="modal-confirm">Confirm</button>
            </div>
        </div>
    </div>
    <header id="header">
        <div class="header-content">
            <a href="#landing" class="logo">Course2Career</a>
            <button class="mobile-menu-btn" id="mobile-menu-btn">
                <span></span>
                <span></span>
                <span></span>
            </button>
            <nav class="nav-links" id="nav-links"></nav>
        </div>
    </header>
    <main>
        <section id="view-landing" class="view-section">
            <div class="hero">
                <div class="container">
                    <h1>Navigate Your Career Path with Confidence</h1>
                    <p>Generate personalized learning roadmaps and visualize your professional journey, all powered by cutting-edge AI technology.</p>
                    <div class="hero-buttons">
                        <a href="#signup" class="btn btn-primary">Get Started Free</a>
                        <a href="#login" class="btn btn-secondary">Sign In</a>
                    </div>
                </div>
            </div>
            <div class="features">
                <div class="container">
                    <div class="section-header">
                        <h2>Everything You Need to Succeed</h2>
                        <p>Powerful tools to help you plan your professional growth and achieve your career goals</p>
                    </div>
                    <div class="feature-grid">
                        <div class="feature-card">
                            <div class="feature-icon">✨</div>
                            <h3>AI Course Generation</h3>
                            <p>Simply describe your learning goal, and our AI instantly creates a comprehensive course outline complete with modules, skills to learn, and realistic salary expectations.</p>
                        </div>
                        <div class="feature-card">
                            <div class="feature-icon">🎯</div>
                            <h3>Career Path Visualization</h3>
                            <p>See the complete picture of your career journey. Our intelligent visualizer maps out typical progressions from entry-level to senior positions in your field.</p>
                        </div>
                        <div class="feature-card">
                            <div class="feature-icon">📚</div>
                            <h3>Save & Track Progress</h3>
                            <p>Keep all your generated courses organized in one place. Save your favorites to your personal dashboard and access them anytime, anywhere.</p>
                        </div>
                    </div>
                </div>
            </div>
        </section>
        <section id="view-login" class="view-section">
            <div class="auth-wrapper">
                <div class="auth-card">
                    <h1>Welcome Back</h1>
                    <p>Sign in to continue your learning journey</p>
                    <form id="login-form">
                        <div class="form-group">
                            <label for="login-email">Email Address</label>
                            <input type="email" id="login-email" name="email" placeholder="you@example.com" required>
                        </div>
                        <div class="form-group">
                            <label for="login-password">Password</label>
                            <input type="password" id="login-password" name="password" placeholder="Enter your password" required>
                        </div>
                        <button type="submit" class="btn btn-primary" style="width: 100%; margin-top: 1rem;">Sign In</button>
                    </form>
                    <div class="auth-footer">
                        <p>Don't have an account? <a href="#signup">Sign Up</a></p>
                    </div>
                </div>
            </div>
        </section>
        <section id="view-signup" class="view-section">
            <div class="auth-wrapper">
                <div class="auth-card">
                    <h1>Create an Account</h1>
                    <p>Start your journey with Course2Career today</p>
                    <form id="signup-form">
                        <div class="form-group">
                            <label for="signup-fullName">Full Name</label>
                            <input type="text" id="signup-fullName" name="fullName" placeholder="John Doe" required>
                        </div>
                        <div class="form-group">
                            <label for="signup-email">Email Address</label>
                            <input type="email" id="signup-email" name="email" placeholder="you@example.com" required>
                        </div>
                        <div class="form-group">
                            <label for="signup-password">Password</label>
                            <input type="password" id="signup-password" name="password" placeholder="Create a strong password" required>
                        </div>
                        <button type="submit" class="btn btn-primary" style="width: 100%; margin-top: 1rem;">Create Account</button>
                    </form>
                    <div class="auth-footer">
                        <p>Already have an account? <a href="#login">Sign In</a></p>
                    </div>
                </div>
            </div>
        </section>
        <section id="view-dashboard" class="view-section">
            <div class="content-section">
                <div class="container">
                    <div class="content-box">
                        <h1>🚀 Course Generator</h1>
                        <p>Describe any skill or career goal, and our AI will craft the perfect learning path for you in seconds.</p>
                        <form id="ai-course-form" class="ai-form">
                            <input type="text" id="ai-course-query" placeholder="e.g., 'Become a product manager' or 'Learn web development'" required>
                            <button type="submit">✨ Generate Course</button>
                        </form>
                        <div id="ai-course-result"></div>
                    </div>
                </div>
            </div>
        </section>
        <section id="view-career-path" class="view-section">
            <div class="content-section">
                <div class="container">
                    <div class="content-box">
                        <h1>🎯 Career Path Visualizer</h1>
                        <p>Enter a career field and discover the typical progression from entry-level to senior positions, complete with salary ranges.</p>
                        <form id="ai-path-form" class="ai-form">
                            <input type="text" id="ai-path-query" placeholder="e.g., 'Software Engineering' or 'Digital Marketing'" required>
                            <button type="submit">🔮 Visualize Path</button>
                        </form>
                        <div id="ai-path-result"></div>
                    </div>
                </div>
            </div>
        </section>
        <section id="view-saved-courses" class="view-section">
            <div class="content-section">
                <div class="container">
                    <div class="section-header" style="text-align: left; margin-bottom: 2rem;">
                        <h2>📚 My Saved Courses</h2>
                        <p>Access all your saved learning paths in one place</p>
                    </div>
                    <div id="saved-courses-content"></div>
                </div>
            </div>
        </section>
        <section id="view-profile" class="view-section">
            <div class="content-section">
                <div class="container" style="max-width: 700px;">
                    <div class="section-header" style="text-align: left; margin-bottom: 2rem;">
                        <h2>👤 My Profile</h2>
                        <p>Update your personal information</p>
                    </div>
                    <div class="content-box">
                        <form id="profile-form">
                            <div class="form-group">
                                <label for="profile-fullName">Full Name</label>
                                <input type="text" id="profile-fullName" required>
                            </div>
                            <div class="form-group">
                                <label for="profile-email">Email Address</label>
                                <input type="email" id="profile-email" required>
                            </div>
                            <button type="submit" class="btn btn-primary">Save Changes</button>
                        </form>
                    </div>
                </div>
            </div>
        </section>
        <section id="view-admin" class="view-section">
            <div class="content-section">
                <div class="container">
                    <div class="section-header" style="text-align: left; margin-bottom: 2rem;">
                        <h2>⚙️ User Management</h2>
                        <p>Manage all registered users</p>
                    </div>
                    <div id="admin-content"></div>
                </div>
            </div>
        </section>
    </main>
    <footer>
        <div class="footer-content">
            <p>&copy; 2025 Course2Career. All rights reserved.</p>
        </div>
    </footer>
    <script>
        const state = {
            token: localStorage.getItem('authToken'),
            userId: localStorage.getItem('userId'),
            role: localStorage.getItem('userRole'),
            savedCourses: []
        };
        const showToast = (message, type = 'error') => {
            const toastContainer = document.getElementById('toast-container');
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            toast.textContent = message;
            toastContainer.appendChild(toast);
            setTimeout(() => {
                toast.style.animation = 'fadeOutRight 0.3s ease';
                setTimeout(() => toast.remove(), 300);
            }, 4000);
        };
        const showModal = (title, message, onConfirm) => {
            const modal = document.getElementById('modal');
            document.getElementById('modal-title').textContent = title;
            document.getElementById('modal-message').textContent = message;
            modal.classList.add('active');
            const confirmHandler = () => {
                onConfirm();
                modal.classList.remove('active');
                document.getElementById('modal-confirm').removeEventListener('click', confirmHandler);
            };
            const cancelHandler = () => {
                modal.classList.remove('active');
                document.getElementById('modal-cancel').removeEventListener('click', cancelHandler);
            };
            document.getElementById('modal-confirm').addEventListener('click', confirmHandler);
            document.getElementById('modal-cancel').addEventListener('click', cancelHandler);
        };
        const apiRequest = async (endpoint, method = 'GET', body = null) => {
            const headers = {
                'Content-Type': 'application/json'
            };
            if (state.token) {
                headers['Authorization'] = `Bearer ${state.token}`;
            }
            const config = {
                method,
                headers
            };
            if (body) {
                config.body = JSON.stringify(body);
            }
            try {
                const response = await fetch(`/api${endpoint}`, config);
                const data = await response.json();
                if (!response.ok) {
                    throw new Error(data.error || 'An unknown error occurred.');
                }
                return data;
            } catch (error) {
                console.error(`API Request Error: ${error.message}`);
                throw error;
            }
        };
        const updateNav = () => {
            const nav = document.getElementById('nav-links');
            const isLoggedIn = !!state.token;
            if (isLoggedIn) {
                nav.innerHTML =
                    `<a href="#dashboard">Dashboard</a>
                    <a href="#career-path">Career Paths</a>
                    <a href="#saved-courses">Saved</a>
                    <a href="#profile">Profile</a>
                    ${state.role === 'admin' ? '<a href="#admin">Admin</a>' : ''}
                    <a href="#" id="logout-btn" class="btn-primary">Logout</a>`;
                document.getElementById('logout-btn').addEventListener('click', (e) => {
                    e.preventDefault();
                    logout();
                });
            } else {
                nav.innerHTML =
                    `<a href="#dashboard">Dashboard</a>
                    <a href="#career-path">Career Paths</a>
                    <a href="#login">Sign In</a>
                    <a href="#signup" class="btn-primary">Sign Up</a>`;
            }
        };
        const logout = () => {
            localStorage.clear();
            state.token = null;
            state.userId = null;
            state.role = null;
            window.location.hash = '#landing';
            router();
        };
        const router = () => {
            const hash = window.location.hash.slice(1) || 'landing';
            const authRoutes = ['login', 'signup'];
            if (state.token && authRoutes.includes(hash)) {
                window.location.hash = '#dashboard';
                return;
            }
            document.querySelectorAll('.view-section').forEach(section => {
                section.classList.remove('active');
            });
            const currentView = document.getElementById(`view-${hash}`);
            if (currentView) {
                currentView.classList.add('active');
                document.querySelectorAll('.nav-links a').forEach(link => {
                    link.classList.remove('active');
                    if (link.getAttribute('href') === `#${hash}`) {
                        link.classList.add('active');
                    }
                });
                if (viewInitializers[hash]) {
                    viewInitializers[hash]();
                }
            } else {
                document.getElementById('view-landing').classList.add('active');
            }
            updateNav();
        };
        const viewInitializers = {
            'login': () => {
                const form = document.getElementById('login-form');
                form.onsubmit = async (e) => {
                    e.preventDefault();
                    const submitBtn = form.querySelector('button[type="submit"]');
                    submitBtn.disabled = true;
                    submitBtn.textContent = 'Signing In...';
                    try {
                        const formData = new FormData(form);
                        const data = await apiRequest('/login', 'POST', {
                            email: formData.get('email'),
                            password: formData.get('password')
                        });
                        state.token = data.token;
                        state.userId = data.userId;
                        state.role = data.role;
                        localStorage.setItem('authToken', data.token);
                        localStorage.setItem('userId', data.userId);
                        localStorage.setItem('userRole', data.role);
                        showToast('Welcome back!', 'success');
                        window.location.hash = '#dashboard';
                        router();
                    } catch (error) {
                        showToast(error.message);
                    } finally {
                        submitBtn.disabled = false;
                        submitBtn.textContent = 'Sign In';
                    }
                };
            },
            'signup': () => {
                const form = document.getElementById('signup-form');
                form.onsubmit = async (e) => {
                    e.preventDefault();
                    const submitBtn = form.querySelector('button[type="submit"]');
                    submitBtn.disabled = true;
                    submitBtn.textContent = 'Creating Account...';
                    try {
                        const formData = new FormData(form);
                        await apiRequest('/signup', 'POST', {
                            fullName: formData.get('fullName'),
                            email: formData.get('email'),
                            password: formData.get('password')
                        });
                        showToast('Account created! Please sign in.', 'success');
                        window.location.hash = '#login';
                        router();
                    } catch (error) {
                        showToast(error.message);
                    } finally {
                        submitBtn.disabled = false;
                        submitBtn.textContent = 'Create Account';
                    }
                };
            },
            'dashboard': () => {
                const form = document.getElementById('ai-course-form');
                const queryInput = document.getElementById('ai-course-query');
                form.onsubmit = async (e) => {
                    e.preventDefault();
                    const resultContainer = document.getElementById('ai-course-result');
                    const submitBtn = form.querySelector('button[type="submit"]');
                    submitBtn.disabled = true;
                    submitBtn.textContent = 'Generating...';
                    resultContainer.innerHTML = '<div class="loading"><div class="spinner"></div><p>Creating your personalized course...</p></div>';
                    try {
                        const courseData = await apiRequest('/generate-course-with-ai', 'POST', { query: queryInput.value });
                        renderCourseCard(courseData, resultContainer, true);
                    } catch (error) {
                        resultContainer.innerHTML = `<p style="text-align:center; color: var(--danger); margin-top: 1rem;">${error.message}</p>`;
                        showToast(error.message);
                    } finally {
                        submitBtn.disabled = false;
                        submitBtn.textContent = '✨ Generate Course';
                    }
                };
            },
            'career-path': () => {
                const form = document.getElementById('ai-path-form');
                const queryInput = document.getElementById('ai-path-query');
                form.onsubmit = async (e) => {
                    e.preventDefault();
                    const resultContainer = document.getElementById('ai-path-result');
                    const submitBtn = form.querySelector('button[type="submit"]');
                    submitBtn.disabled = true;
                    submitBtn.textContent = 'Visualizing...';
                    resultContainer.innerHTML = '<div class="loading"><div class="spinner"></div><p>Mapping your career path...</p></div>';
                    try {
                        const pathData = await apiRequest('/generate-career-path', 'POST', { query: queryInput.value });
                        renderCareerPath(pathData, resultContainer);
                    } catch (error) {
                        resultContainer.innerHTML = `<p style="text-align:center; color: var(--danger); margin-top: 1rem;">${error.message}</p>`;
                        showToast(error.message);
                    } finally {
                        submitBtn.disabled = false;
                        submitBtn.textContent = '🔮 Visualize Path';
                    }
                };
            },
            'saved-courses': async () => {
                if (!state.token) {
                    document.getElementById('saved-courses-content').innerHTML = '<div class="content-box" style="text-align: center; padding: 4rem 2rem;"><h3>Please Sign In</h3><p>Sign in to view and manage your saved courses.</p><a href="#login" class="btn btn-primary" style="margin-top: 1.5rem;">Sign In</a></div>';
                    return;
                }
                const container = document.getElementById('saved-courses-content');
                container.innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading your saved courses...</p></div>';
                try {
                    const courses = await apiRequest('/saved-courses');
                    state.savedCourses = courses;
                    if (courses.length === 0) {
                        container.innerHTML = '<div class="content-box" style="text-align: center; padding: 4rem 2rem;"><h3>No Saved Courses Yet</h3><p>Start generating courses and save your favorites!</p><a href="#dashboard" class="btn btn-primary" style="margin-top: 1.5rem;">Generate Your First Course</a></div>';
                        return;
                    }
                    container.innerHTML = `<div class="saved-layout"><div class="saved-sidebar"><h3>Your Courses</h3><div class="saved-list" id="saved-list"></div></div><div class="saved-display" id="saved-display"><p style="text-align:center; padding: 4rem 0; color: var(--text-secondary);">Select a course to view its details.</p></div></div>`;
                    const listContainer = document.getElementById('saved-list');
                    courses.forEach((course, index) => {
                        const btn = document.createElement('button');
                        btn.className = 'saved-item';
                        btn.textContent = course.course_title;
                        btn.dataset.courseId = course.id;
                        btn.onclick = () => {
                            document.querySelectorAll('.saved-item').forEach(b => b.classList.remove('active'));
                            btn.classList.add('active');
                            renderCourseCard(JSON.parse(course.course_data), document.getElementById('saved-display'), false, course.id);
                        };
                        listContainer.appendChild(btn);
                        if (index === 0) {
                            btn.click();
                        }
                    });
                } catch (error) {
                    container.innerHTML = `<p style="text-align:center; color: var(--danger);">${error.message}</p>`;
                    showToast(error.message);
                }
            },
            'profile': async () => {
                if (!state.token) return;
                try {
                    const user = await apiRequest('/profile');
                    document.getElementById('profile-fullName').value = user.full_name;
                    document.getElementById('profile-email').value = user.email;
                } catch (error) {
                    showToast('Could not load profile');
                }
                const form = document.getElementById('profile-form');
                form.onsubmit = async (e) => {
                    e.preventDefault();
                    const submitBtn = form.querySelector('button[type="submit"]');
                    submitBtn.disabled = true;
                    submitBtn.textContent = 'Saving...';
                    try {
                        await apiRequest('/profile', 'PUT', {
                            fullName: document.getElementById('profile-fullName').value,
                            email: document.getElementById('profile-email').value
                        });
                        showToast('Profile updated successfully!', 'success');
                    } catch (error) {
                        showToast(error.message);
                    } finally {
                        submitBtn.disabled = false;
                        submitBtn.textContent = 'Save Changes';
                    }
                };
            },
            'admin': async () => {
                if (state.role !== 'admin') {
                    document.getElementById('admin-content').innerHTML = '<div class="content-box" style="text-align: center; padding: 4rem 2rem;"><h3>Access Denied</h3><p>You do not have permission to view this page.</p></div>';
                    return;
                }
                const container = document.getElementById('admin-content');
                container.innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading users...</p></div>';
                try {
                    const users = await apiRequest('/users');
                    renderAdminTable(users, container);
                } catch (error) {
                    container.innerHTML = `<p style="text-align:center; color: var(--danger);">${error.message}</p>`;
                    showToast(error.message);
                }
            }
        };
        const renderCourseCard = (course, container, showSaveBtn, courseId = null) => {
            const isSaved = state.savedCourses.some(c => c.course_title === course.title);
            let actionButtonHtml = '';
            if (state.token) {
                if (showSaveBtn) {
                    if (isSaved) {
                        actionButtonHtml = '<button class="btn btn-primary" style="margin-top: 2rem; width: 100%;" disabled>✓ Saved</button>';
                    } else {
                        actionButtonHtml = '<button class="btn btn-primary" id="save-course-btn" style="margin-top: 2rem; width: 100%;">💾 Save This Course</button>';
                    }
                } else if (courseId) {
                    actionButtonHtml = `<button class="btn btn-secondary" id="delete-saved-course-btn" style="background: var(--danger); color: white; border: none; margin-top: 2rem; width: 100%;">🗑️ Delete From Saved</button>`;
                }
            }
            container.innerHTML = `<div class="course-card"><div class="course-header"><h3>${course.title}</h3><p>${course.description}</p></div><div class="course-stats"><div class="stat-item"><span class="stat-label">Salary Range</span><span class="stat-value">${course.startingSalary}</span></div><div class="stat-item"><span class="stat-label">Duration</span><span class="stat-value">${course.duration}</span></div><div class="stat-item"><span class="stat-label">Difficulty</span><span class="stat-value">${course.difficulty}</span></div></div><div class="skills-section"><h4>Skills You'll Learn</h4><ul class="skills-list">${course.skills.map(skill => `<li class="skill-tag">${skill}</li>`).join('')}</ul></div><div class="modules-section"><h4>Course Modules</h4><div class="module-list">${course.modules.map(module => `<div class="module-item"><h5>${module.title}</h5><p>${module.description}</p></div>`).join('')}</div></div>${actionButtonHtml}</div>`;
            if (showSaveBtn && state.token && !isSaved) {
                document.getElementById('save-course-btn').onclick = async (e) => {
                    e.target.disabled = true;
                    e.target.textContent = 'Saving...';
                    try {
                        await apiRequest('/saved-courses', 'POST', {
                            courseData: course
                        });
                        showToast('Course saved successfully!', 'success');
                        e.target.textContent = '✓ Saved';
                        const savedCourses = await apiRequest('/saved-courses');
                        state.savedCourses = savedCourses;
                    } catch (error) {
                        showToast(error.message);
                        e.target.disabled = false;
                        e.target.textContent = '💾 Save This Course';
                    }
                };
            }
            if (!showSaveBtn && courseId) {
                document.getElementById('delete-saved-course-btn').onclick = () => {
                    showModal('Delete Course?', `Are you sure you want to delete "${course.title}"?`, async () => {
                        try {
                            await apiRequest(`/saved-courses/${courseId}`, 'DELETE');
                            showToast('Course deleted successfully', 'success');
                            viewInitializers['saved-courses']();
                        } catch (error) {
                            showToast(error.message);
                        }
                    });
                };
            }
        };
        const renderCareerPath = (data, container) => {
            const stages = {
                'Entry Level': [],
                'Mid Career': [],
                'Late Career': []
            };
            if (data.flowchart && data.flowchart.roles) {
                data.flowchart.roles.forEach(role => {
                    if (stages[role.stage]) {
                        stages[role.stage].push(role);
                    }
                });
            }
            container.innerHTML = `<div class="career-path-container"><div class="path-header"><h2>${data.title}</h2><p>${data.description}</p></div><div class="career-stages">${Object.entries(stages).map(([stageName, roles]) => `<div class="career-stage ${stageName.toLowerCase().replace(' ', '')}"><div class="stage-header"><h3>${stageName}</h3></div>${roles.map(role => `<div class="role-card"><div class="role-title">${role.title}</div><div class="role-salary">${role.salary}</div></div>`).join('')}</div>`).join('')}</div></div>`;
        };
        const renderAdminTable = (users, container) => {
            container.innerHTML = `<div class="content-box" style="padding: 0; overflow-x: auto;"><table class="admin-table"><thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Joined</th><th>Actions</th></tr></thead><tbody>${users.map(user => `<tr><td>${user.full_name}</td><td>${user.email}</td><td><span style="text-transform: capitalize;">${user.role}</span></td><td>${new Date(user.created_at).toLocaleDateString()}</td><td>${user.id.toString() !== state.userId ? `<button class="delete-btn" data-id="${user.id}">Delete</button>` : '<span style="color: var(--text-light);">—</span>'}</td></tr>`).join('')}</tbody></table></div>`;
            container.querySelectorAll('.delete-btn').forEach(btn => {
                btn.onclick = () => {
                    showModal('Delete User?', 'This action cannot be undone. All user data will be permanently deleted.', async () => {
                        try {
                            await apiRequest(`/users/${btn.dataset.id}`, 'DELETE');
                            showToast('User deleted successfully', 'success');
                            viewInitializers['admin']();
                        } catch (error) {
                            showToast(error.message);
                        }
                    });
                };
            });
        };
        document.getElementById('mobile-menu-btn').addEventListener('click', () => {
            document.getElementById('nav-links').classList.toggle('active');
        });
        window.addEventListener('scroll', () => {
            if (window.scrollY > 50) {
                document.getElementById('header').classList.add('scrolled');
            } else {
                document.getElementById('header').classList.remove('scrolled');
            }
        });
        window.addEventListener('hashchange', router);
        window.addEventListener('DOMContentLoaded', router);
    </script>
</body>
</html>
