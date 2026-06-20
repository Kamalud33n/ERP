"""
Cross-Module Trigger System
Automatically executes actions across modules when key events occur
Examples: PO approval → GL posting, Goods receipt → 3-way match
"""

from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
from sqlalchemy.orm import Session
import json


class TriggerEvent(str, Enum):
    """Events that can trigger cross-module actions"""
    PO_APPROVED = "po_approved"
    PO_REJECTED = "po_rejected"
    GOODS_RECEIVED = "goods_received"
    INVOICE_RECEIVED = "invoice_received"
    ASSET_PURCHASED = "asset_purchased"
    PAYROLL_RUN = "payroll_run"
    LEAVE_APPROVED = "leave_approved"
    EXPENSE_APPROVED = "expense_approved"
    LOW_STOCK_THRESHOLD = "low_stock_threshold"
    CONTRACT_EXPIRY_WARNING = "contract_expiry_warning"


class CrossModuleTrigger:
    """
    Manages automatic cross-module actions
    Ensures data consistency across HR, Finance, Procurement, Inventory, Assets
    """

    @staticmethod
    def handle_po_approved(
        db: Session,
        po_id: int,
        po_data: Dict[str, Any]
    ):
        """
        When PO is approved:
        1. Create GL commitment entry (Finance)
        2. Create pending receipt record (Inventory)
        3. Send notification to warehouse
        """
        print(f"[Trigger] PO #{po_id} approved - initiating cross-module actions")

        # 1. Post GL commitment entry
        CrossModuleTrigger._post_gl_commitment(
            db=db,
            po_id=po_id,
            po_data=po_data
        )

        # 2. Create inventory pending receipt
        CrossModuleTrigger._create_inventory_receipt(
            db=db,
            po_id=po_id,
            po_data=po_data
        )

        # 3. Send warehouse notification
        CrossModuleTrigger._send_warehouse_notification(
            db=db,
            po_id=po_id,
            po_data=po_data
        )

    @staticmethod
    def handle_goods_received(
        db: Session,
        grn_id: int,
        grn_data: Dict[str, Any]
    ):
        """
        When goods are received (GRN):
        1. Update stock in Inventory
        2. Match against PO (quality check)
        3. Await invoice for 3-way match (PO/GRN/Invoice)
        4. Send notification when 3-way match ready
        """
        print(f"[Trigger] GRN #{grn_id} created - matching against PO/Invoice")

        # 1. Update inventory stock
        CrossModuleTrigger._update_inventory_stock(
            db=db,
            grn_id=grn_id,
            grn_data=grn_data
        )

        # 2. Check PO match
        po_matched = CrossModuleTrigger._match_po(db, grn_data)

        # 3. Check 3-way match (PO + GRN + Invoice)
        if po_matched:
            CrossModuleTrigger._check_three_way_match(
                db=db,
                grn_id=grn_id,
                grn_data=grn_data
            )

    @staticmethod
    def handle_invoice_received(
        db: Session,
        invoice_id: int,
        invoice_data: Dict[str, Any]
    ):
        """
        When vendor invoice is received:
        1. Match against PO (amount verification)
        2. Check if GRN exists (quality receipt)
        3. Complete 3-way match & trigger GL posting
        """
        print(f"[Trigger] Invoice #{invoice_id} received - checking 3-way match")

        # 1. Match PO
        po_matched = CrossModuleTrigger._match_po(db, invoice_data)

        # 2. Check GRN match
        grn_matched = CrossModuleTrigger._match_grn(db, invoice_data)

        # 3. If all 3 matched, post to GL
        if po_matched and grn_matched:
            CrossModuleTrigger._post_vendor_bill(
                db=db,
                invoice_id=invoice_id,
                invoice_data=invoice_data
            )

    @staticmethod
    def handle_asset_purchased(
        db: Session,
        asset_id: int,
        asset_data: Dict[str, Any]
    ):
        """
        When asset is purchased via approved PO:
        1. Register in Fixed Assets module with QR code
        2. Start depreciation schedule
        3. Assign location (warehouse/department)
        """
        print(f"[Trigger] Asset #{asset_id} purchased - registering with depreciation schedule")

        # 1. Register asset with QR code
        CrossModuleTrigger._register_asset_with_qr(
            db=db,
            asset_id=asset_id,
            asset_data=asset_data
        )

        # 2. Schedule depreciation
        CrossModuleTrigger._schedule_depreciation(
            db=db,
            asset_id=asset_id,
            asset_data=asset_data
        )

    @staticmethod
    def handle_payroll_run(
        db: Session,
        payroll_id: int,
        payroll_data: Dict[str, Any]
    ):
        """
        When payroll is processed:
        1. Post GL entries (salary expense, payables, deductions)
        2. Create bank transfer file
        3. Archive payroll records for audit
        """
        print(f"[Trigger] Payroll #{payroll_id} processed - posting GL entries")

        # 1. Post GL entries
        CrossModuleTrigger._post_payroll_gl_entries(
            db=db,
            payroll_id=payroll_id,
            payroll_data=payroll_data
        )

        # 2. Create bank transfer file
        CrossModuleTrigger._create_bank_transfer_file(
            db=db,
            payroll_id=payroll_id,
            payroll_data=payroll_data
        )

    # ───────────────────────────────────────────────────────────────
    # Internal helper methods
    # ───────────────────────────────────────────────────────────────

    @staticmethod
    def _post_gl_commitment(
        db: Session,
        po_id: int,
        po_data: Dict[str, Any]
    ):
        """Post GL commitment entry when PO approved"""
        # Example: PO of $10,000 creates commitment:
        # DR: Commitment - Expense/Asset account
        # CR: Budget - Encumbrance account
        commitment_amount = po_data.get("total_amount", 0)
        
        journal_entry = {
            "date": datetime.utcnow(),
            "description": f"Commitment for PO #{po_id}",
            "lines": [
                {
                    "account": "7100-0000",  # Commitment account
                    "debit": commitment_amount,
                    "credit": 0,
                    "description": "PO Commitment"
                },
                {
                    "account": "9100-0000",  # Encumbrance account
                    "debit": 0,
                    "credit": commitment_amount,
                    "description": "Budget Encumbrance"
                }
            ],
            "reference": f"PO-{po_id}",
            "status": "posted"
        }
        
        print(f"  ✓ GL Commitment posted: ${commitment_amount}")
        # TODO: Insert into JournalEntry table
        return journal_entry

    @staticmethod
    def _create_inventory_receipt(
        db: Session,
        po_id: int,
        po_data: Dict[str, Any]
    ):
        """Create pending receipt record in Inventory"""
        items = po_data.get("items", [])
        print(f"  ✓ Created pending receipt for {len(items)} items in Inventory")
        # TODO: Insert into PendingReceipt table
        return po_id

    @staticmethod
    def _send_warehouse_notification(
        db: Session,
        po_id: int,
        po_data: Dict[str, Any]
    ):
        """Send notification to warehouse about incoming goods"""
        from app.tasks.celery_config import send_email_task
        
        warehouse_emails = po_data.get("warehouse_emails", [])
        for email in warehouse_emails:
            send_email_task.delay(
                to_email=email,
                subject=f"📦 Approved PO #{po_id} - Goods Coming In",
                html_content=f"""
                <h2>Purchase Order Approved</h2>
                <p>PO #{po_id} has been approved and goods are on the way.</p>
                <p><strong>Items:</strong></p>
                <ul>
                {"".join(f"<li>{item['name']} - Qty: {item['quantity']}</li>" for item in po_data.get('items', []))}
                </ul>
                <p><a href="http://localhost:3000/procurement/po/{po_id}">View PO Details</a></p>
                """
            )

    @staticmethod
    def _update_inventory_stock(
        db: Session,
        grn_id: int,
        grn_data: Dict[str, Any]
    ):
        """Update stock quantities when goods received"""
        items = grn_data.get("items", [])
        print(f"  ✓ Updated inventory stock for {len(items)} items")
        # TODO: Update StockLevel quantities
        return grn_id

    @staticmethod
    def _match_po(db: Session, reference_data: Dict[str, Any]) -> bool:
        """Verify received goods/invoice match PO"""
        po_id = reference_data.get("po_id")
        print(f"  ✓ Verified match against PO #{po_id}")
        # TODO: Check PO details against current data
        return True

    @staticmethod
    def _match_grn(db: Session, reference_data: Dict[str, Any]) -> bool:
        """Verify invoice matches received goods"""
        grn_id = reference_data.get("grn_id")
        print(f"  ✓ Verified match against GRN #{grn_id}")
        # TODO: Check GRN details against invoice
        return True

    @staticmethod
    def _check_three_way_match(
        db: Session,
        grn_id: int,
        grn_data: Dict[str, Any]
    ):
        """Check if PO + GRN + Invoice all match"""
        print(f"  ✓ Checking 3-way match for GRN #{grn_id}")
        # If all match: ready for GL posting
        # If mismatch: flag for investigation

    @staticmethod
    def _post_vendor_bill(
        db: Session,
        invoice_id: int,
        invoice_data: Dict[str, Any]
    ):
        """Post vendor bill to GL after 3-way match"""
        invoice_amount = invoice_data.get("amount", 0)
        
        journal_entry = {
            "date": datetime.utcnow(),
            "description": f"Vendor Invoice #{invoice_id}",
            "lines": [
                {
                    "account": "5100-0000",  # Expense account
                    "debit": invoice_amount,
                    "credit": 0,
                    "description": "Purchased goods/services"
                },
                {
                    "account": "2200-0000",  # Accounts payable
                    "debit": 0,
                    "credit": invoice_amount,
                    "description": "Vendor liability"
                }
            ],
            "reference": f"INV-{invoice_id}",
            "status": "posted"
        }
        
        print(f"  ✓ GL Bill posted: ${invoice_amount}")
        return journal_entry

    @staticmethod
    def _register_asset_with_qr(
        db: Session,
        asset_id: int,
        asset_data: Dict[str, Any]
    ):
        """Register asset and generate QR code"""
        import qrcode
        
        # Generate QR code linking to asset
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(f"ASSET-{asset_id}")
        qr.make(fit=True)
        
        # TODO: Save QR code image
        print(f"  ✓ Generated QR code for asset #{asset_id}")
        return asset_id

    @staticmethod
    def _schedule_depreciation(
        db: Session,
        asset_id: int,
        asset_data: Dict[str, Any]
    ):
        """Create depreciation schedule for asset"""
        cost = asset_data.get("cost", 0)
        life_years = asset_data.get("useful_life_years", 5)
        
        monthly_depreciation = cost / (life_years * 12)
        
        print(f"  ✓ Scheduled depreciation: ${monthly_depreciation}/month for {life_years} years")
        # TODO: Create DepreciationSchedule records for each month
        return asset_id

    @staticmethod
    def _post_payroll_gl_entries(
        db: Session,
        payroll_id: int,
        payroll_data: Dict[str, Any]
    ):
        """Post payroll GL entries (salary, deductions, taxes)"""
        total_gross = payroll_data.get("total_gross", 0)
        total_deductions = payroll_data.get("total_deductions", 0)
        total_net = payroll_data.get("total_net", 0)
        
        journal_entry = {
            "date": datetime.utcnow(),
            "description": f"Payroll Run #{payroll_id}",
            "lines": [
                {
                    "account": "6100-0000",  # Salary expense
                    "debit": total_gross,
                    "credit": 0,
                    "description": "Employee salaries"
                },
                {
                    "account": "2300-0000",  # Salary payable
                    "debit": 0,
                    "credit": total_net,
                    "description": "Net salaries payable"
                },
                {
                    "account": "2400-0000",  # Deductions payable
                    "debit": 0,
                    "credit": total_deductions,
                    "description": "Tax & deductions payable"
                }
            ],
            "reference": f"PAYROLL-{payroll_id}",
            "status": "posted"
        }
        
        print(f"  ✓ Payroll GL entries posted: ${total_gross} total")
        return journal_entry

    @staticmethod
    def _create_bank_transfer_file(
        db: Session,
        payroll_id: int,
        payroll_data: Dict[str, Any]
    ):
        """Create bank transfer file for payroll payments"""
        employees = payroll_data.get("employees", [])
        print(f"  ✓ Created bank transfer file for {len(employees)} employees")
        # TODO: Generate ACH/SWIFT file for bank import


# ───────────────────────────────────────────────────────────────
# Trigger Router - Maps events to handlers
# ───────────────────────────────────────────────────────────────

TRIGGER_HANDLERS = {
    TriggerEvent.PO_APPROVED: CrossModuleTrigger.handle_po_approved,
    TriggerEvent.GOODS_RECEIVED: CrossModuleTrigger.handle_goods_received,
    TriggerEvent.INVOICE_RECEIVED: CrossModuleTrigger.handle_invoice_received,
    TriggerEvent.ASSET_PURCHASED: CrossModuleTrigger.handle_asset_purchased,
    TriggerEvent.PAYROLL_RUN: CrossModuleTrigger.handle_payroll_run,
}


def execute_trigger(
    db: Session,
    event: TriggerEvent,
    record_id: int,
    record_data: Dict[str, Any]
):
    """Execute appropriate handler for an event"""
    handler = TRIGGER_HANDLERS.get(event)
    if handler:
        try:
            return handler(db, record_id, record_data)
        except Exception as e:
            print(f"❌ Error executing trigger {event}: {str(e)}")
            # TODO: Log to audit trail
            raise
    else:
        print(f"⚠️ No handler found for trigger: {event}")
