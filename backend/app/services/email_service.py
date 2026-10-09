"""
Email notification service using Resend.

Provides:
  - send_review_alert: triggered after each AI review for users who opted in
  - send_monthly_digest: sent on the 1st of each month via Celery Beat

Resend SDK is imported lazily so that the service can be imported without
the SDK installed (it will just log a warning and skip).
"""

import html as _html
import logging
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


def _resend_client():
    """Return a configured Resend client, or None if the API key is not set."""
    if not settings.resend_api_key:
        logger.warning("RESEND_API_KEY not configured — email not sent")
        return None
    try:
        import resend
        resend.api_key = settings.resend_api_key
        return resend
    except ImportError:
        logger.warning("resend package not installed — email not sent")
        return None


def _score_label(score: float) -> str:
    if score >= 70:
        return "✅ Passed"
    if score >= 40:
        return "⚠️ Needs Attention"
    return "❌ Failed"


def send_review_alert(
    to: list[str],
    repo_full_name: str,
    pr_number: int,
    pr_title: str,
    pr_author: str,
    score_overall: float,
    score_requirement: float,
    score_security: float,
    score_quality: float,
    score_performance: float,
    critical_issues: list[str],
    pr_url: str,
) -> None:
    """
    Send a PR review alert email.
    Called synchronously from Celery tasks — no async.
    """
    resend = _resend_client()
    if resend is None or not to:
        return

    safe_repo = _html.escape(repo_full_name)
    safe_title = _html.escape(pr_title)
    safe_author = _html.escape(pr_author)
    safe_pr_url = _html.escape(pr_url)

    issues_html = (
        "<ul>" + "".join(f"<li>{_html.escape(i)}</li>" for i in critical_issues) + "</ul>"
        if critical_issues
        else "<p><em>No critical issues.</em></p>"
    )

    html = f"""
<html><body style="font-family:sans-serif;color:#1f2937;max-width:600px;margin:0 auto">
  <h2 style="color:#2563eb">🤖 CodeIntel Review: {safe_repo}</h2>
  <p>PR <strong><a href="{safe_pr_url}">#{pr_number}: {safe_title}</a></strong> by @{safe_author}</p>

  <table style="border-collapse:collapse;width:100%;margin:16px 0">
    <tr style="background:#f3f4f6">
      <th style="text-align:left;padding:8px 12px;font-size:12px;text-transform:uppercase;color:#6b7280">Dimension</th>
      <th style="text-align:right;padding:8px 12px;font-size:12px;text-transform:uppercase;color:#6b7280">Score</th>
    </tr>
    <tr><td style="padding:8px 12px;border-top:1px solid #e5e7eb">Overall</td>
        <td style="padding:8px 12px;border-top:1px solid #e5e7eb;text-align:right;font-weight:600">
          {score_overall:.0f}/100 {_score_label(score_overall)}</td></tr>
    <tr style="background:#f9fafb"><td style="padding:8px 12px">Requirement</td>
        <td style="padding:8px 12px;text-align:right">{score_requirement:.0f}/100</td></tr>
    <tr><td style="padding:8px 12px;border-top:1px solid #e5e7eb">Security</td>
        <td style="padding:8px 12px;border-top:1px solid #e5e7eb;text-align:right">{score_security:.0f}/100</td></tr>
    <tr style="background:#f9fafb"><td style="padding:8px 12px">Code Quality</td>
        <td style="padding:8px 12px;text-align:right">{score_quality:.0f}/100</td></tr>
    <tr><td style="padding:8px 12px;border-top:1px solid #e5e7eb">Performance</td>
        <td style="padding:8px 12px;border-top:1px solid #e5e7eb;text-align:right">{score_performance:.0f}/100</td></tr>
  </table>

  <h3 style="color:#dc2626">🚨 Critical Issues</h3>
  {issues_html}

  <p style="margin-top:24px">
    <a href="{safe_pr_url}" style="background:#2563eb;color:#fff;padding:10px 20px;border-radius:6px;text-decoration:none;font-weight:600">
      View PR on GitHub
    </a>
  </p>
  <hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0"/>
  <p style="color:#9ca3af;font-size:12px">
    CodeIntel AI Review · You're receiving this because you have review alerts enabled.
  </p>
</body></html>
"""

    try:
        resend.Emails.send({
            "from": settings.email_from,
            "to": to,
            "subject": f"[CodeIntel] PR #{pr_number} scored {score_overall:.0f}/100 — {repo_full_name}",
            "html": html,
        })
        logger.info("Review alert sent to %d recipient(s) for %s#%d", len(to), repo_full_name, pr_number)
    except Exception as exc:
        logger.warning("Failed to send review alert email: %s", exc)


def send_monthly_digest(
    to: list[str],
    repo_full_name: str,
    total_reviews: int,
    avg_overall: float,
    avg_security: float,
    avg_quality: float,
    avg_requirement: float,
    avg_performance: float,
    top_authors: list[dict[str, Any]],
    month_label: str,
) -> None:
    """
    Send the monthly digest email.
    Called synchronously from the Celery Beat task.
    """
    resend = _resend_client()
    if resend is None or not to:
        return

    safe_repo = _html.escape(repo_full_name)
    safe_month = _html.escape(month_label)

    authors_rows = "".join(
        f"""<tr style="{'background:#f9fafb' if i % 2 else ''}">
          <td style="padding:6px 12px">#{i+1}</td>
          <td style="padding:6px 12px">@{_html.escape(a['author'])}</td>
          <td style="padding:6px 12px;text-align:center">{a['pr_count']}</td>
          <td style="padding:6px 12px;text-align:right;font-weight:600">{a['avg_overall']:.1f}</td>
        </tr>"""
        for i, a in enumerate(top_authors[:10])
    )

    html = f"""
<html><body style="font-family:sans-serif;color:#1f2937;max-width:600px;margin:0 auto">
  <h2 style="color:#2563eb">🤖 CodeIntel Monthly Digest — {safe_month}</h2>
  <p>Repository: <strong>{safe_repo}</strong></p>

  <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin:16px 0">
    <div style="background:#eff6ff;border-radius:8px;padding:16px">
      <div style="font-size:28px;font-weight:700;color:#2563eb">{total_reviews}</div>
      <div style="font-size:13px;color:#6b7280">PRs reviewed</div>
    </div>
    <div style="background:#f0fdf4;border-radius:8px;padding:16px">
      <div style="font-size:28px;font-weight:700;color:#16a34a">{avg_overall:.1f}</div>
      <div style="font-size:13px;color:#6b7280">Avg overall score</div>
    </div>
  </div>

  <table style="border-collapse:collapse;width:100%;margin:16px 0">
    <tr style="background:#f3f4f6">
      <th style="text-align:left;padding:8px 12px;font-size:12px;text-transform:uppercase;color:#6b7280">Dimension</th>
      <th style="text-align:right;padding:8px 12px;font-size:12px;text-transform:uppercase;color:#6b7280">Avg Score</th>
    </tr>
    <tr><td style="padding:8px 12px;border-top:1px solid #e5e7eb">Requirement</td>
        <td style="padding:8px 12px;border-top:1px solid #e5e7eb;text-align:right">{avg_requirement:.1f}</td></tr>
    <tr style="background:#f9fafb"><td style="padding:8px 12px">Security</td>
        <td style="padding:8px 12px;text-align:right">{avg_security:.1f}</td></tr>
    <tr><td style="padding:8px 12px;border-top:1px solid #e5e7eb">Code Quality</td>
        <td style="padding:8px 12px;border-top:1px solid #e5e7eb;text-align:right">{avg_quality:.1f}</td></tr>
    <tr style="background:#f9fafb"><td style="padding:8px 12px">Performance</td>
        <td style="padding:8px 12px;text-align:right">{avg_performance:.1f}</td></tr>
  </table>

  {'<h3>🏆 Top Authors</h3><table style="border-collapse:collapse;width:100%"><tr style="background:#f3f4f6"><th style="text-align:left;padding:8px 12px;font-size:12px;text-transform:uppercase;color:#6b7280">Rank</th><th style="text-align:left;padding:8px 12px;font-size:12px;text-transform:uppercase;color:#6b7280">Author</th><th style="text-align:center;padding:8px 12px;font-size:12px;text-transform:uppercase;color:#6b7280">PRs</th><th style="text-align:right;padding:8px 12px;font-size:12px;text-transform:uppercase;color:#6b7280">Avg</th></tr>' + authors_rows + '</table>' if top_authors else ''}

  <hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0"/>
  <p style="color:#9ca3af;font-size:12px">
    CodeIntel AI Review · Monthly digest for {safe_month}.
  </p>
</body></html>
"""

    try:
        resend.Emails.send({
            "from": settings.email_from,
            "to": to,
            "subject": f"[CodeIntel] Monthly Digest — {month_label} — {repo_full_name}",
            "html": html,
        })
        logger.info("Monthly digest sent to %d recipient(s) for %s", len(to), repo_full_name)
    except Exception as exc:
        logger.warning("Failed to send monthly digest email: %s", exc)
