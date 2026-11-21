"""POST /api/contact on the portfolio: the message is saved, then e-mailed to the owner after the answer."""

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Request

from ... import crud
from ...models import ContactIn
from ...utils import mail
from ..deps import SessionDep, SettingsDep, Submit, Submitted, done, maintenance

router = APIRouter(prefix="/api", dependencies=[Depends(maintenance)])


@router.post("/contact")
def contact(request: Request, form: Annotated[Submitted[ContactIn], Depends(Submit(ContactIn, "contact"))],
            settings: SettingsDep, session: SessionDep, tasks: BackgroundTasks):
    if not form.data.is_bot:  # a bot gets the same answer; nothing is stored
        lead = crud.save_lead(session, form.data, request.state.lang)
        tasks.add_task(mail.notify_owner, settings, f"lead #{lead.id}", *mail.compose("lead", lead=lead), lead.email)
    return done(request, form, "/contact?sent=1")
