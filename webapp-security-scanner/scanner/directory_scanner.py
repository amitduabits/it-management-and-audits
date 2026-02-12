"""
Directory and File Enumeration Scanner
==========================================
Checks for exposed sensitive directories, files, and endpoints
that should not be publicly accessible.

Categories:
- Administrative panels and interfaces
- Configuration and environment files
- Backup and archive files
- Version control directories (.git, .svn)
- API documentation and debug endpoints
- Server status and information pages
- Default installation files
- Log files and database dumps

OWASP Reference: A01:2021 - Broken Access Control
               A05:2021 - Security Misconfiguration
CWE Reference: CWE-538 (File and Directory Information Exposure)

ETHICAL USE ONLY: Only scan systems you own or have written authorization to test.
"""

import time
import requests
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed


@dataclass
class DirectoryFinding:
    """Represents an exposed directory or file finding."""
    url: str
    path: str
    status_code: int
    content_length: int
    category: str
    severity: str
    description: str
    recommendation: str
    owasp_category: str
    cwe_id: str


@dataclass
class DirectoryScanResult:
    """Complete result of a directory enumeration scan."""
    target_url: str
    findings: List[DirectoryFinding] = field(default_factory=list)
    paths_checked: int = 0
    paths_found: int = 0
    scan_duration: float = 0.0
    errors: List[str] = field(default_factory=list)


# -----------------------------------------------------------------------
# Directory and file wordlist organized by category
# -----------------------------------------------------------------------

SCAN_PATHS = {
    # Administrative panels
    'admin_panels': {
        'category': 'Administrative Panel',
        'severity': 'High',
        'owasp': 'A01:2021 - Broken Access Control',
        'cwe': 'CWE-284',
        'description': (
            'Administrative panel is accessible. This may allow unauthorized '
            'users to modify application settings, manage users, or access '
            'sensitive functionality.'
        ),
        'recommendation': (
            'Restrict admin panel access by IP whitelist, VPN, or strong '
            'authentication with MFA. Remove default admin paths.'
        ),
        'paths': [
            '/admin',
            '/admin/',
            '/administrator',
            '/admin/login',
            '/admin/dashboard',
            '/admin/panel',
            '/wp-admin',
            '/wp-admin/',
            '/cpanel',
            '/phpmyadmin',
            '/phpmyadmin/',
            '/adminer',
            '/adminer.php',
            '/manager',
            '/management',
            '/admin.php',
            '/admin.html',
            '/controlpanel',
            '/dashboard',
            '/webadmin',
        ],
    },

    # Configuration files
    'config_files': {
        'category': 'Configuration File',
        'severity': 'Critical',
        'owasp': 'A05:2021 - Security Misconfiguration',
        'cwe': 'CWE-538',
        'description': (
            'Configuration file is publicly accessible. May expose database '
            'credentials, API keys, secret keys, and other sensitive settings.'
        ),
        'recommendation': (
            'Move configuration files outside the web root. Configure the '
            'web server to deny access to configuration files. Use environment '
            'variables for sensitive settings.'
        ),
        'paths': [
            '/.env',
            '/.env.local',
            '/.env.production',
            '/.env.development',
            '/.env.backup',
            '/config.php',
            '/config.yml',
            '/config.yaml',
            '/config.json',
            '/configuration.php',
            '/settings.py',
            '/settings.json',
            '/wp-config.php',
            '/web.config',
            '/application.properties',
            '/application.yml',
            '/appsettings.json',
            '/database.yml',
            '/credentials.json',
            '/secrets.json',
            '/config/database.yml',
            '/config/secrets.yml',
        ],
    },

    # Version control
    'version_control': {
        'category': 'Version Control',
        'severity': 'Critical',
        'owasp': 'A05:2021 - Security Misconfiguration',
        'cwe': 'CWE-538',
        'description': (
            'Version control directory is exposed. Attackers can download '
            'the entire source code, including hardcoded credentials, '
            'API keys, and proprietary logic.'
        ),
        'recommendation': (
            'Remove version control directories from production servers. '
            'Configure web server rules to deny access to .git, .svn, etc.'
        ),
        'paths': [
            '/.git',
            '/.git/',
            '/.git/HEAD',
            '/.git/config',
            '/.git/index',
            '/.gitignore',
            '/.svn',
            '/.svn/',
            '/.svn/entries',
            '/.hg',
            '/.hg/',
            '/.bzr',
            '/.cvs',
        ],
    },

    # Backup files
    'backup_files': {
        'category': 'Backup File',
        'severity': 'High',
        'owasp': 'A05:2021 - Security Misconfiguration',
        'cwe': 'CWE-530',
        'description': (
            'Backup file is publicly accessible. May contain source code, '
            'database dumps, or configuration data with credentials.'
        ),
        'recommendation': (
            'Remove backup files from web-accessible directories. Store '
            'backups in a secure location outside the web root with proper '
            'access controls.'
        ),
        'paths': [
            '/backup',
            '/backup/',
            '/backups',
            '/backups/',
            '/backup.sql',
            '/backup.zip',
            '/backup.tar.gz',
            '/db_backup.sql',
            '/database.sql',
            '/dump.sql',
            '/site_backup.zip',
            '/backup.bak',
            '/data.sql',
            '/export.sql',
            '/old/',
            '/temp/',
            '/tmp/',
        ],
    },

    # API and debug endpoints
    'api_endpoints': {
        'category': 'API/Debug Endpoint',
        'severity': 'Medium',
        'owasp': 'A01:2021 - Broken Access Control',
        'cwe': 'CWE-200',
        'description': (
            'API or debug endpoint is accessible. May expose internal data, '
            'user information, or application internals.'
        ),
        'recommendation': (
            'Protect API endpoints with authentication. Disable debug '
            'endpoints in production. Implement proper access controls.'
        ),
        'paths': [
            '/api',
            '/api/',
            '/api/v1',
            '/api/v2',
            '/api/users',
            '/api/config',
            '/api/debug',
            '/api/status',
            '/api/health',
            '/api/info',
            '/swagger',
            '/swagger/',
            '/swagger.json',
            '/swagger-ui',
            '/swagger-ui.html',
            '/api-docs',
            '/api-docs/',
            '/openapi.json',
            '/graphql',
            '/graphiql',
            '/debug',
            '/debug/',
            '/trace',
            '/actuator',
            '/actuator/health',
            '/actuator/env',
            '/_debug',
            '/__debug__',
        ],
    },

    # Server information
    'server_info': {
        'category': 'Server Information',
        'severity': 'Low',
        'owasp': 'A05:2021 - Security Misconfiguration',
        'cwe': 'CWE-200',
        'description': (
            'Server information page is accessible. Reveals server '
            'configuration, PHP settings, or other technical details '
            'useful for reconnaissance.'
        ),
        'recommendation': (
            'Remove or restrict access to server information pages. '
            'Disable directory listing. Remove default installation files.'
        ),
        'paths': [
            '/server-status',
            '/server-info',
            '/phpinfo.php',
            '/info.php',
            '/test.php',
            '/robots.txt',
            '/sitemap.xml',
            '/crossdomain.xml',
            '/clientaccesspolicy.xml',
            '/humans.txt',
            '/security.txt',
            '/.well-known/security.txt',
            '/status',
            '/health',
            '/ping',
            '/version',
            '/readme.html',
            '/README.md',
            '/CHANGELOG.md',
            '/LICENSE',
        ],
    },

    # Log files
    'log_files': {
        'category': 'Log File',
        'severity': 'High',
        'owasp': 'A09:2021 - Security Logging and Monitoring Failures',
        'cwe': 'CWE-532',
        'description': (
            'Log file is publicly accessible. May contain sensitive '
            'information including IP addresses, usernames, session tokens, '
            'API keys, and error details.'
        ),
        'recommendation': (
            'Move log files outside the web root. Configure web server '
            'to deny access to log files. Implement proper log management.'
        ),
        'paths': [
            '/logs',
            '/logs/',
            '/log',
            '/log/',
            '/error.log',
            '/access.log',
            '/debug.log',
            '/application.log',
            '/app.log',
            '/error_log',
            '/wp-content/debug.log',
        ],
    },

    # Common CMS and framework files
    'cms_framework': {
        'category': 'CMS/Framework File',
        'severity': 'Low',
        'owasp': 'A06:2021 - Vulnerable and Outdated Components',
        'cwe': 'CWE-200',
        'description': (
            'CMS or framework specific file detected. Reveals the '
            'technology stack used, which helps attackers find known '
            'vulnerabilities.'
        ),
        'recommendation': (
            'Remove unnecessary default files. Keep the CMS/framework '
            'updated to the latest version. Restrict access to internal files.'
        ),
        'paths': [
            '/wp-login.php',
            '/wp-content/',
            '/wp-includes/',
            '/xmlrpc.php',
            '/wp-json/',
            '/wp-cron.php',
            '/joomla/',
            '/drupal/',
            '/magento/',
            '/laravel/',
            '/symfony/',
            '/django/',
            '/rails/',
            '/static/',
            '/assets/',
            '/media/',
            '/uploads/',
            '/uploads',
            '/files/',
            '/files',
        ],
    },
}


def _check_path(
    base_url: str,
    path: str,
    category_config: Dict,
    timeout: int = 10
) -> Optional[DirectoryFinding]:
    """
    Check if a single path is accessible.

    Args:
        base_url: Target base URL
        path: Path to check
        category_config: Category configuration dict
        timeout: Request timeout

    Returns:
        DirectoryFinding if accessible, None otherwise
    """
    url = urljoin(base_url.rstrip('/') + '/', path.lstrip('/'))

    try:
        response = requests.get(
            url,
            timeout=timeout,
            allow_redirects=False,
            verify=False,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                              'AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/120.0.0.0 Safari/537.36'
            }
        )

        # Consider these status codes as "found"
        # 200: OK, 301/302: Redirect (resource exists), 401/403: Protected
        if response.status_code in [200, 301, 302, 401, 403]:
            # Determine severity based on status code
            severity = category_config['severity']
            if response.status_code in [401, 403]:
                # Protected but exists - lower severity
                severity = 'Low' if severity != 'Critical' else 'Medium'
                description = (
                    f"Path exists but is protected (HTTP {response.status_code}). "
                    f"{category_config['description']}"
                )
            else:
                description = category_config['description']

            return DirectoryFinding(
                url=url,
                path=path,
                status_code=response.status_code,
                content_length=len(response.content),
                category=category_config['category'],
                severity=severity,
                description=description,
                recommendation=category_config['recommendation'],
                owasp_category=category_config['owasp'],
                cwe_id=category_config['cwe'],
            )

    except requests.exceptions.ConnectionError:
        pass
    except requests.exceptions.Timeout:
        pass
    except requests.exceptions.RequestException:
        pass

    return None


def scan_directories(
    target_url: str,
    categories: Optional[List[str]] = None,
    custom_paths: Optional[List[str]] = None,
    timeout: int = 10,
    max_threads: int = 20,
    verbose: bool = False
) -> DirectoryScanResult:
    """
    Run a directory enumeration scan against the target.

    Args:
        target_url: Base URL of the target application
        categories: List of categories to scan (None = all)
                    Options: admin_panels, config_files, version_control,
                             backup_files, api_endpoints, server_info,
                             log_files, cms_framework
        custom_paths: Additional custom paths to check
        timeout: Request timeout in seconds
        max_threads: Maximum concurrent threads
        verbose: Enable verbose output

    Returns:
        DirectoryScanResult with all findings
    """
    start_time = time.time()

    result = DirectoryScanResult(target_url=target_url)

    # Build list of paths to check
    paths_to_check = []  # List of (path, category_config) tuples

    selected_categories = categories or list(SCAN_PATHS.keys())

    for cat_name in selected_categories:
        if cat_name in SCAN_PATHS:
            cat_config = SCAN_PATHS[cat_name]
            for path in cat_config['paths']:
                paths_to_check.append((path, cat_config))

    # Add custom paths
    if custom_paths:
        custom_config = {
            'category': 'Custom Path',
            'severity': 'Medium',
            'owasp': 'A01:2021 - Broken Access Control',
            'cwe': 'CWE-538',
            'description': 'Custom path is accessible.',
            'recommendation': 'Review if this path should be publicly accessible.',
        }
        for path in custom_paths:
            paths_to_check.append((path, custom_config))

    result.paths_checked = len(paths_to_check)

    print(f"[*] Starting directory enumeration scan...")
    print(f"[*] Target: {target_url}")
    print(f"[*] Categories: {', '.join(selected_categories)}")
    print(f"[*] Paths to check: {len(paths_to_check)}")
    print(f"[*] Threads: {max_threads}")
    print()

    # Execute scan with thread pool
    checked_count = 0

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = {
            executor.submit(
                _check_path, target_url, path, config, timeout
            ): (path, config)
            for path, config in paths_to_check
        }

        for future in as_completed(futures):
            path, config = futures[future]
            checked_count += 1

            try:
                finding = future.result()
                if finding:
                    result.findings.append(finding)
                    result.paths_found += 1

                    severity_icon = {
                        'Critical': '[!!]',
                        'High': '[!]',
                        'Medium': '[*]',
                        'Low': '[.]',
                        'Informational': '[-]',
                    }.get(finding.severity, '[?]')

                    print(
                        f"  {severity_icon} FOUND: {finding.path} "
                        f"(HTTP {finding.status_code}) "
                        f"[{finding.category}] "
                        f"[{finding.severity}]"
                    )

                elif verbose:
                    print(f"  [-] Not found: {path}")

            except Exception as e:
                result.errors.append(f"{path}: {str(e)}")

            # Progress update every 50 paths
            if not verbose and checked_count % 50 == 0:
                print(
                    f"  [*] Progress: {checked_count}/{len(paths_to_check)} "
                    f"paths checked, {result.paths_found} found..."
                )

    # Sort findings by severity
    severity_order = {'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3, 'Informational': 4}
    result.findings.sort(key=lambda f: severity_order.get(f.severity, 5))

    result.scan_duration = time.time() - start_time

    print()
    print(f"[*] Directory scan complete")
    print(f"[*] Duration: {result.scan_duration:.2f}s")
    print(f"[*] Paths checked: {result.paths_checked}")
    print(f"[*] Paths found: {result.paths_found}")

    return result


def format_directory_report(result: DirectoryScanResult) -> str:
    """Format the directory scan result as a text report."""
    lines = [
        "=" * 70,
        "  DIRECTORY ENUMERATION REPORT",
        "=" * 70,
        f"  Target: {result.target_url}",
        f"  Paths Checked: {result.paths_checked}",
        f"  Paths Found: {result.paths_found}",
        f"  Duration: {result.scan_duration:.2f}s",
        "=" * 70,
        "",
    ]

    if result.findings:
        lines.append(f"  {'PATH':<30s} {'STATUS':<8s} {'CATEGORY':<22s} {'SEVERITY'}")
        lines.append("  " + "-" * 75)

        for finding in result.findings:
            lines.append(
                f"  {finding.path:<30s} {finding.status_code:<8d} "
                f"{finding.category:<22s} {finding.severity}"
            )
    else:
        lines.append("  No exposed directories or files found.")

    lines.append("")
    return "\n".join(lines)


if __name__ == '__main__':
    import sys

    target = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:5000'
    verbose = '--verbose' in sys.argv

    result = scan_directories(target, verbose=verbose)
    print()
    print(format_directory_report(result))
