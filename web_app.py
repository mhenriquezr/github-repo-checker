#!/usr/bin/env python3
"""Web interface for GitHub Repository Checker."""
from flask import Flask, render_template, request, jsonify
from github_client import GitHubClient
from verifier import RepositoryVerifier
import traceback
import config

app = Flask(__name__)

def apply_settings(settings):
    """Apply settings from frontend to config."""
    if 'minStars' in settings:
        config.MIN_STARS = int(settings['minStars'])
    if 'minContributors' in settings:
        config.MIN_CONTRIBUTORS = int(settings['minContributors'])
    if 'minFiles' in settings:
        config.MIN_FILES = int(settings['minFiles'])
    if 'minDirectories' in settings:
        config.MIN_DIRECTORIES = int(settings['minDirectories'])
    if 'maxSizeMB' in settings:
        config.MAX_SIZE_MB = int(settings['maxSizeMB'])
    if 'activityDays' in settings:
        config.ACTIVITY_DAYS = int(settings['activityDays'])
    if 'passThreshold' in settings:
        config.PASS_THRESHOLD = int(settings['passThreshold'])

@app.route('/')
def index():
    """Main page."""
    return render_template('index.html')

@app.route('/api/verify', methods=['POST'])
def verify_repo():
    """Verify a repository."""
    try:
        data = request.get_json()
        repo_url = data.get('repo_url', '').strip()
        settings = data.get('settings', {})
        
        if not repo_url:
            return jsonify({'error': 'Repository URL is required'}), 400
        
        # Apply settings if provided
        if settings:
            apply_settings(settings)
        
        client = GitHubClient()
        verifier = RepositoryVerifier(client)
        
        report = verifier.verify_repository(repo_url)
        
        # Convert to dict
        failed_checks = report.get_failed_checks()
        warnings = report.get_warnings()
        passed_checks = [c for c in report.checks if c.passed and c.severity == 'error']
        
        result = {
            'repository': {
                'name': report.repository.full_name,
                'url': report.repository.url,
                'language': report.repository.language,
                'stars': report.repository.stars,
                'license': report.repository.license,
                'description': report.repository.description,
            },
            'score': report.score,
            'passed': report.passed,
            'summary': report.summary,
            'checks': [
                {
                    'name': check.name,
                    'passed': check.passed,
                    'message': check.message,
                    'severity': check.severity
                }
                for check in report.checks
            ],
            'failed_checks': [
                {
                    'name': check.name,
                    'message': check.message
                }
                for check in failed_checks
            ],
            'warnings': [
                {
                    'name': check.name,
                    'message': check.message
                }
                for check in warnings
            ],
            'passed_checks': [
                {
                    'name': check.name,
                    'message': check.message
                }
                for check in passed_checks
            ]
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/approved', methods=['GET'])
def get_approved_repos():
    """Get list of approved repositories."""
    try:
        from approved_repos import APPROVED_REPOS
        return jsonify({
            'repos': APPROVED_REPOS,
            'count': len(APPROVED_REPOS)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/verify-single', methods=['POST'])
def verify_single_from_batch():
    """Verify a single repository (for batch processing)."""
    try:
        data = request.get_json()
        repo_url = data.get('repo_url', '').strip()
        settings = data.get('settings', {})
        
        if not repo_url:
            return jsonify({'error': 'Repository URL is required'}), 400
        
        # Apply settings if provided
        if settings:
            apply_settings(settings)
        
        client = GitHubClient()
        verifier = RepositoryVerifier(client)
        
        try:
            report = verifier.verify_repository(repo_url)
            failed_checks = report.get_failed_checks()
            warnings = report.get_warnings()
            passed_checks = [c for c in report.checks if c.passed and c.severity == 'error']
            
            result = {
                'url': repo_url,
                'name': report.repository.full_name,
                'score': report.score,
                'passed': report.passed,
                'stars': report.repository.stars,
                'language': report.repository.language,
                'failed_count': len(failed_checks),
                'warning_count': len(warnings),
                'passed_count': len(passed_checks),
                'failed_checks': [{'name': c.name, 'message': c.message} for c in failed_checks],
                'warnings': [{'name': c.name, 'message': c.message} for c in warnings],
                'passed_checks': [{'name': c.name, 'message': c.message} for c in passed_checks]
            }
        except Exception as e:
            result = {
                'url': repo_url,
                'name': repo_url.split('/')[-1],
                'error': str(e),
                'passed': False,
                'score': 0
            }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search', methods=['POST'])
def search_repos():
    """Search repositories."""
    try:
        data = request.get_json()
        settings = data.get('settings', {})
        
        # Apply settings if provided
        if settings:
            apply_settings(settings)
        
        client = GitHubClient()
        verifier = RepositoryVerifier(client)
        
        # Build search query
        query_parts = []
        topics = data.get('topics', [])
        language = data.get('language')
        min_stars = data.get('min_stars', 3)
        min_contributors = data.get('min_contributors', 3)
        max_results = min(data.get('max_results', 10), 20)
        verify = data.get('verify', False)
        repo_age_months = data.get('repo_age_months')
        
        # Add keywords to search in name, description, readme
        if topics:
            # Search for keywords in general (not just topics)
            keywords = ' '.join(topics)
            query_parts.append(keywords)
        
        # Add age filter if specified
        if repo_age_months:
            from datetime import datetime, timedelta, timezone
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=repo_age_months * 30)
            date_str = cutoff_date.strftime('%Y-%m-%d')
            query_parts.append(f'created:>={date_str}')
        
        query = ' '.join(query_parts) if query_parts else 'stars:>0'
        
        # Search repositories
        repos = client.search_repositories(
            query=query,
            language=language,
            min_stars=min_stars,
            max_results=max_results * 3  # Get more to filter
        )
        
        results = []
        for repo in repos:
            # Filter by contributors
            contributors_count = client.get_contributors_count(repo)
            if contributors_count < min_contributors:
                continue
            
            repo_info = client.get_repo_info(repo)
            
            if verify:
                try:
                    report = verifier.verify_repository(repo.html_url)
                    if report.passed:
                        results.append({
                            'name': repo_info.full_name,
                            'url': repo_info.url,
                            'language': repo_info.language,
                            'stars': repo_info.stars,
                            'license': repo_info.license,
                            'score': report.score
                        })
                except Exception as e:
                    # Skip repositories that fail verification
                    continue
            else:
                results.append({
                    'name': repo_info.full_name,
                    'url': repo_info.url,
                    'language': repo_info.language,
                    'stars': repo_info.stars,
                    'license': repo_info.license,
                    'score': None
                })
            
            if len(results) >= max_results:
                break
        
        # Sort by stars if not verified
        if not verify:
            results.sort(key=lambda x: x['stars'] or 0, reverse=True)
        else:
            results.sort(key=lambda x: x['score'] or 0, reverse=True)
        
        return jsonify({'results': results})
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
