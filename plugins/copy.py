from __future__ import annotations

import os
import re
import json
from pyrogram import Client, Filters
from helpers import gDrive_sql as db
from helpers.utils import humanbytes
from plugins.token import getIdFromUrl
from helpers import parent_id_sql as sql
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

G_DRIVE_DIR_MIME_TYPE = "application/vnd.google-apps.folder"
G_DRIVE_FILE_LINK = "https://drive.google.com/open?id={}"
G_DRIVE_FOLDER_LINK = "https://drive.google.com/drive/folders/{}"



def getFilesByFolderId(service, folder_id):
    page_token = None
    q = f"'{folder_id}' in parents"
    files = []
    while True:
        response = service.files().list(supportsTeamDrives=True,
                                               includeTeamDriveItems=True,
                                               q=q,
                                               spaces='drive',
                                               pageSize=200,
                                               fields='nextPageToken, files(id, name, mimeType,size)',
                                               pageToken=page_token).execute()
        for file in response.get('files', []):
            files.append(file)
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break
    return files


def copyFile(service, file_id, dest_id):
    body = {
        'parents': [dest_id]
    }

    try:
        res = service.files().copy(supportsAllDrives=True,fileId=file_id,body=body).execute()
        return res
    except HttpError as err:
        if err.resp.get('content-type', '').startswith('application/json'):
            reason = json.loads(err.content).get('error').get('errors')[0].get('reason')
            if reason == 'userRateLimitExceeded' or reason == 'dailyLimitExceeded':
               return 'LimitExceeded'
            else:
               return 'error'


def clone_folder(
    service,
    folder_id: str,
    parent_id: str | None,
    *,
    transferred_size: int = 0,
) -> tuple[str, int]:
    """Recursively clone a Google-Drive folder.

    Parameters
    ----------
    service : Resource
        Google-Drive service instance.
    folder_id : str
        ID of the source folder that needs to be cloned.
    parent_id : str | None
        ID of the destination parent directory (where the clone should live).
    transferred_size : int, optional
        Accumulator for the total size of the files copied so far. This value
        is updated on every recursive call and returned.

    Returns
    -------
    tuple[str, int]
        (new_folder_id, total_size_copied)
    """

    files = getFilesByFolderId(service, folder_id)

    # Return early for empty folders so that the parent stays intact.
    if not files:
        return parent_id, transferred_size

    new_folder_id = parent_id

    for item in files:
        mime_type = item.get("mimeType")
        item_id = item.get("id")
        item_name = item.get("name")

        if mime_type == G_DRIVE_DIR_MIME_TYPE:
            # Create the corresponding directory in the destination and
            # recurse into it.
            child_dir_id = create_directory(service, item_name, parent_id)
            new_folder_id, transferred_size = clone_folder(
                service,
                item_id,
                child_dir_id,
                transferred_size=transferred_size,
            )
        else:
            try:
                transferred_size += int(item.get("size", 0))
            except (TypeError, ValueError):
                pass

            copyFile(service, item_id, parent_id)

    return new_folder_id, transferred_size

def create_directory(service, directory_name, parent_id):
        file_metadata = {
            "name": directory_name,
            "mimeType": G_DRIVE_DIR_MIME_TYPE
        }
        if parent_id is not None:
            file_metadata["parents"] = [parent_id]
        file = service.files().create(supportsTeamDrives=True, body=file_metadata).execute()
        file_id = file.get("id")
        return file_id



@Client.on_message(Filters.private & Filters.incoming & Filters.command(['copy']))
async def _copy(client, message):
  creds = db.get_credential(message.from_user.id)
  if creds is None:
    await message.reply_text('❗ **Not an authorized user.**\n__Authorize your Google Drive Account by  running /auth Command in order to use this bot.__', quote=True)
    return
  if sql.get_id(message.from_user.id):
    parent_id = sql.get_id(message.from_user.id).parent_id
  else:
    parent_id = 'root'
  transferred_size = 0
  if len(message.command) > 1:
    sent_message = await message.reply_text('**Checking Google Drive Link...**', quote=True)
    file_id = getIdFromUrl(message.command[1])
    if file_id == 'NotFound':
      await sent_message.edit('❗ **Invalid Google Drive URL**\n__Only Google Drive links can be copied.__')
      return
    else:
      await sent_message.edit(f'🗂️ **Cloning to Google Drive...**\n__{file_id}__')
    service = build(
        "drive",
        "v3",
        credentials=creds,
        cache_discovery=False
      )
    try:
      meta = service.files().get(supportsAllDrives=True, fileId=file_id, fields="name,id,mimeType,size").execute()
    except HttpError as err:
      if err.resp.get('content-type', '').startswith('application/json'):
            reason = json.loads(err.content).get('error').get('errors')[0].get('reason')
            if 'notFound' in reason:
               await sent_message.edit('❗**ERROR: FILE NOT FOUND**\n__Make sure the file exists and accessible by the account you authenticated.__')
            else:
               await sent_message.edit(f"**ERROR:** ```{str(err).replace('>', '').replace('<', '')}```")
    except Exception as e:
      await sent_message.edit(f"**ERROR:** ```{str(e).replace('>', '').replace('<', '')}```")
    if meta.get("mimeType") == G_DRIVE_DIR_MIME_TYPE:
       dir_id = create_directory(service, meta.get('name'), parent_id)
       try:
         _, transferred_size = clone_folder(service, meta.get('id'), dir_id)
         await sent_message.edit(f"✅ **Copied successfully.**\n[{meta.get('name')}]({G_DRIVE_FOLDER_LINK.format(dir_id)}) __({humanbytes(transferred_size)})__")
       except Exception as e:
         await sent_message.edit(f'**ERROR:** ```{e}```')
    else:
      try:
         file = copyFile(service, meta.get('id'), parent_id)
         await sent_message.edit(f"✅ **Copied successfully.**\n[{file.get('name')}]({G_DRIVE_FILE_LINK.format(file.get('id'))}) __({humanbytes(int(meta.get('size')))})__")
      except Exception as e:
         await sent_message.edit(f'**ERROR:** ```{e}```')
  else:
    await message.reply_text('**Copy Google Drive Files or Folder**\n__Copy GDrive Files/Folder to your Google Drive Account. Use__ ```/copy {GDriveFolderURL/FileURL}``` __for copying.__')