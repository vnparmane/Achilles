from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models.party import Party


class PartyService:
    def __init__(self, session: Session):
        self.session = session

    def _next_code(self, prefix: str) -> str:
        result = self.session.execute(
            select(Party.code)
            .where(Party.code.like(f"{prefix}%"))
            .order_by(Party.code.desc())
        ).first()
        if result is None:
            return f"{prefix}001"
        last_code = result[0]
        last_num = int(last_code[len(prefix):]) if last_code[len(prefix):].isdigit() else 0
        return f"{prefix}{last_num + 1:03d}"

    def create_party(
        self,
        name: str,
        party_type: str,
        gstin: str | None = None,
        state: str | None = None,
        state_code: str | None = None,
        registration_type: str = "regular",
        address: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        opening_balance: float = 0.0,
    ) -> Party:
        prefix = "C" if party_type == "customer" else "V" if party_type == "vendor" else "P"
        code = self._next_code(prefix)
        party = Party(
            code=code,
            name=name,
            party_type=party_type,
            gstin=gstin,
            state=state,
            state_code=state_code,
            registration_type=registration_type,
            address=address,
            phone=phone,
            email=email,
            opening_balance=opening_balance,
        )
        self.session.add(party)
        self.session.commit()
        return party

    def get_all_parties(self, party_type: str | None = None) -> list[Party]:
        query = select(Party).order_by(Party.name)
        if party_type:
            query = query.where(Party.party_type.in_([party_type, "both"]))
        return list(self.session.scalars(query).all())

    def get_party_by_id(self, party_id: int) -> Party | None:
        return self.session.get(Party, party_id)

    def update_party(self, party_id: int, **kwargs) -> Party | None:
        party = self.session.get(Party, party_id)
        if party is None:
            return None
        for key, value in kwargs.items():
            setattr(party, key, value)
        self.session.commit()
        return party

    def delete_party(self, party_id: int) -> bool:
        party = self.session.get(Party, party_id)
        if party is None:
            return False
        try:
            self.session.delete(party)
            self.session.commit()
            return True
        except Exception:
            self.session.rollback()
            raise

    def search_parties(self, query: str) -> list[Party]:
        stmt = select(Party).where(
            Party.name.ilike(f"%{query}%") | Party.code.ilike(f"%{query}%")
        ).order_by(Party.name)
        return list(self.session.scalars(stmt).all())
