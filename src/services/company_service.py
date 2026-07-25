from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models.company import Company


class CompanyService:
    def __init__(self, session: Session):
        self.session = session

    def has_company(self) -> bool:
        return self.session.scalar(select(Company.id)) is not None

    def get_company(self) -> Company | None:
        return self.session.scalar(select(Company))

    def create_company(
        self,
        name: str,
        gstin: str | None = None,
        address: str | None = None,
        state: str | None = None,
        state_code: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        bank_name: str | None = None,
        bank_branch: str | None = None,
        bank_account_no: str | None = None,
        bank_ifsc: str | None = None,
    ) -> Company:
        company = Company(
            name=name,
            gstin=gstin,
            address=address,
            state=state,
            state_code=state_code,
            phone=phone,
            email=email,
            bank_name=bank_name,
            bank_branch=bank_branch,
            bank_account_no=bank_account_no,
            bank_ifsc=bank_ifsc,
        )
        self.session.add(company)
        self.session.commit()
        return company

    def update_company(self, company_id: int, **kwargs) -> Company | None:
        company = self.session.get(Company, company_id)
        if company is None:
            return None
        for key, value in kwargs.items():
            setattr(company, key, value)
        self.session.commit()
        return company
