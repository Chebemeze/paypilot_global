"""
PayPilot Global — Smart Onboarding Rescue
Classifies stuck employees and generates fix-it messages.
"""
from __future__ import annotations

from typing import Optional

from app.models import Employee


# ─── Issue Classification ─────────────────────────────────────────────────────

def classify_employee_issue(employee: Employee) -> Optional[dict]:
    """
    Analyze an employee's onboarding state and return a structured
    rescue message with admin explanation and employee-facing messages.
    """
    status = employee.onboarding_status
    kyc = employee.kyc_status
    wallet = employee.wallet_status

    # Already ready — no issue
    if status == "READY":
        return None

    # Suspended or deleted
    if status == "SUSPENDED":
        return _build_issue(
            issue="EMPLOYEE_SUSPENDED",
            severity="HIGH",
            admin_explanation=f"{employee.full_name} has been suspended from the platform.",
            recommended_action="Review the suspension reason and reactivate if appropriate.",
            email_msg=(
                f"Hi {employee.full_name.split()[0]}, your account has been suspended. "
                f"Please contact your HR team for more information."
            ),
            whatsapp_msg=(
                f"Hi {employee.full_name.split()[0]}, your payroll account is currently suspended. "
                f"Please reach out to HR."
            ),
        )

    # Invite not accepted
    if status == "INVITED":
        return _build_issue(
            issue="INVITE_NOT_ACCEPTED",
            severity="MEDIUM",
            admin_explanation=(
                f"{employee.full_name} was invited but has not yet accepted the BMONI app invitation."
            ),
            recommended_action="Resend the invitation or follow up directly with the employee.",
            email_msg=(
                f"Hi {employee.full_name.split()[0]}, you have a pending invitation to set up your "
                f"salary wallet. Please check your email and accept the invitation so we can process "
                f"your payroll."
            ),
            whatsapp_msg=(
                f"Hi {employee.full_name.split()[0]}, please accept your salary wallet invitation "
                f"so payroll can begin. Check your email for the link."
            ),
        )

    # Linked but KYC not started or pending
    if status == "LINKED":
        return _build_issue(
            issue="KYC_INCOMPLETE",
            severity="MEDIUM",
            admin_explanation=(
                f"{employee.full_name} has linked their account but hasn't completed KYC verification yet."
            ),
            recommended_action="Send a reminder to complete identity verification in the BMONI app.",
            email_msg=(
                f"Hi {employee.full_name.split()[0]}, your salary wallet setup requires identity "
                f"verification. Please open the BMONI app and complete the verification steps so "
                f"payroll can process your salary."
            ),
            whatsapp_msg=(
                f"Hi {employee.full_name.split()[0]}, please complete your identity verification "
                f"in the BMONI app to activate your salary wallet."
            ),
        )

    # KYC pending
    if status == "KYC_PENDING":
        return _build_issue(
            issue="KYC_UNDER_REVIEW",
            severity="LOW",
            admin_explanation=(
                f"{employee.full_name}'s KYC is submitted and under review. "
                f"This usually resolves within 24-48 hours."
            ),
            recommended_action="No action needed. Monitor for KYC completion or action required.",
            email_msg=(
                f"Hi {employee.full_name.split()[0]}, your identity verification is being reviewed. "
                f"We'll notify you once it's complete."
            ),
            whatsapp_msg=(
                f"Hi {employee.full_name.split()[0]}, your KYC is being processed. "
                f"You'll get a notification when it's ready."
            ),
        )

    # KYC action required
    if status == "KYC_ACTION_REQUIRED":
        if kyc == "selfie_liveness_required":
            return _build_issue(
                issue="KYC_ACTION_REQUIRED",
                severity="MEDIUM",
                admin_explanation=(
                    f"{employee.full_name} needs to complete liveness verification (selfie)."
                ),
                recommended_action="Send a reminder to complete selfie verification in the BMONI app.",
                email_msg=(
                    f"Hi {employee.full_name.split()[0]}, your salary wallet setup is almost complete. "
                    f"Please open the BMONI app and complete the selfie verification step so payroll "
                    f"can process your salary."
                ),
                whatsapp_msg=(
                    f"Hi {employee.full_name.split()[0]}, please complete selfie verification in "
                    f"BMONI so your salary wallet can be activated."
                ),
            )
        elif kyc == "bvn_mismatch":
            return _build_issue(
                issue="BVN_NAME_MISMATCH",
                severity="HIGH",
                admin_explanation=(
                    f"{employee.full_name}'s BVN name doesn't match their registered name. "
                    f"This is common and usually requires the employee to verify their BVN details."
                ),
                recommended_action="Ask the employee to verify their BVN details match their profile.",
                email_msg=(
                    f"Hi {employee.full_name.split()[0]}, there's a mismatch between your BVN "
                    f"details and your profile. Please open the BMONI app and verify your information "
                    f"matches your BVN records."
                ),
                whatsapp_msg=(
                    f"Hi {employee.full_name.split()[0]}, please check your BVN details in the "
                    f"BMONI app — there's a name mismatch that needs fixing."
                ),
            )
        else:
            return _build_issue(
                issue="KYC_ACTION_REQUIRED",
                severity="MEDIUM",
                admin_explanation=(
                    f"{employee.full_name} needs to take action to complete KYC. "
                    f"Reason: {kyc or 'not specified'}."
                ),
                recommended_action="Send a reminder to check the BMONI app for required actions.",
                email_msg=(
                    f"Hi {employee.full_name.split()[0]}, there are pending actions needed to "
                    f"complete your salary wallet setup. Please open the BMONI app for details."
                ),
                whatsapp_msg=(
                    f"Hi {employee.full_name.split()[0]}, please check the BMONI app — there are "
                    f"steps needed to activate your salary wallet."
                ),
            )

    # Wallet pending
    if status == "WALLET_PENDING":
        return _build_issue(
            issue="WALLET_NOT_PROVISIONED",
            severity="MEDIUM",
            admin_explanation=(
                f"{employee.full_name}'s KYC is complete but the wallet hasn't been fully provisioned yet."
            ),
            recommended_action="Check the BMONI dashboard for wallet provisioning status. May resolve automatically.",
            email_msg=(
                f"Hi {employee.full_name.split()[0]}, your identity verification is complete! "
                f"Your salary wallet is being set up. You'll be notified once it's ready."
            ),
            whatsapp_msg=(
                f"Hi {employee.full_name.split()[0]}, your wallet is being set up. "
                f"You'll get a notification when it's ready for payroll."
            ),
        )

    # Unknown / default
    return _build_issue(
        issue="UNKNOWN_ISSUE",
        severity="LOW",
        admin_explanation=(
            f"{employee.full_name}'s status is {status}. Unable to classify the specific issue."
        ),
        recommended_action="Check the BMONI API for detailed onboarding status.",
        email_msg=(
            f"Hi {employee.full_name.split()[0]}, please check your BMONI app for any "
            f"pending actions on your salary wallet."
        ),
        whatsapp_msg=(
            f"Hi {employee.full_name.split()[0]}, please check the BMONI app for "
            f"pending wallet setup steps."
        ),
    )


def _build_issue(
    issue: str,
    severity: str,
    admin_explanation: str,
    recommended_action: str,
    email_msg: str,
    whatsapp_msg: str,
) -> dict:
    return {
        "issue": issue,
        "severity": severity,
        "admin_explanation": admin_explanation,
        "recommended_action": recommended_action,
        "employee_email_message": email_msg,
        "employee_whatsapp_message": whatsapp_msg,
    }
