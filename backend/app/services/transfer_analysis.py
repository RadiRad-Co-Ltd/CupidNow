from collections import defaultdict

from app.services.parser import TransferRecord


def compute_transfer_analysis(parsed: dict) -> dict | None:
    """Compute transfer statistics between the two chat participants.

    All 3 LINE transfer formats represent money flow between the same two people.
    Returns a simple summary: per-person total sent, total count, and overall total.
    """
    transfers: list[TransferRecord] = parsed.get("transfers", [])
    if not transfers:
        return None

    total_amount = 0
    total_count = len(transfers)
    sent: dict[str, int] = defaultdict(int)
    count: dict[str, int] = defaultdict(int)

    for t in transfers:
        total_amount += t.amount
        if t.sender:
            sent[t.sender] += t.amount
            count[t.sender] += 1

    per_person = {}
    for person in parsed["persons"]:
        per_person[person] = {
            "sent": sent.get(person, 0),
            "count": count.get(person, 0),
        }

    return {
        "totalAmount": total_amount,
        "totalCount": total_count,
        "perPerson": per_person,
    }
