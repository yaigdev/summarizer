import os
import datapane as dp
import libsql_client
import pandas as pd
import asyncio
import string
from datetime import datetime, timedelta
from dataclasses import dataclass
from dataclasses_json import DataClassJsonMixin
from typing import List

@dataclass
class YAIGAttachments(DataClassJsonMixin):
    urls: List[str]

img_token = "[:attachments]"

icon_design = {
    "actor": {
        "color": "bg-slate-400",
        "icon": """<svg class="h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M10 8a3 3 0 100-6 3 3 0 000 6zM3.465 14.493a1.23 1.23 0 00.41 1.412A9.957 9.957 0 0010 18c2.31 0 4.438-.784 6.131-2.1.43-.333.604-.903.408-1.41a7.002 7.002 0 00-13.074.003z" /></svg>""",
    },
    "thumbs-up": {
        "color": "bg-indigo-500",
        "icon": """<svg class="h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M1 8.25a1.25 1.25 0 112.5 0v7.5a1.25 1.25 0 11-2.5 0v-7.5zM11 3V1.7c0-.268.14-.526.395-.607A2 2 0 0114 3c0 .995-.182 1.948-.514 2.826-.204.54.166 1.174.744 1.174h2.52c1.243 0 2.261 1.01 2.146 2.247a23.864 23.864 0 01-1.341 5.974C17.153 16.323 16.072 17 14.9 17h-3.192a3 3 0 01-1.341-.317l-2.734-1.366A3 3 0 006.292 15H5V8h.963c.685 0 1.258-.483 1.612-1.068a4.011 4.011 0 012.166-1.73c.432-.143.853-.386 1.011-.814.16-.432.248-.9.248-1.388z" /></svg>""",
    },
    "code": {
        "color": "bg-amber-500",
        "icon": """<svg class="h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"> <path fill-rule="evenodd" d="M4.25 2A2.25 2.25 0 002 4.25v11.5A2.25 2.25 0 004.25 18h11.5A2.25 2.25 0 0018 15.75V4.25A2.25 2.25 0 0015.75 2H4.25zm4.03 6.28a.75.75 0 00-1.06-1.06L4.97 9.47a.75.75 0 000 1.06l2.25 2.25a.75.75 0 001.06-1.06L6.56 10l1.72-1.72zm4.5-1.06a.75.75 0 10-1.06 1.06L13.44 10l-1.72 1.72a.75.75 0 101.06 1.06l2.25-2.25a.75.75 0 000-1.06l-2.25-2.25z" clip-rule="evenodd" /></svg>""",
    },
    "check": {
        "color": "bg-emerald-500",
        "icon": """<svg class="h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path fill-rule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" clip-rule="evenodd" /></svg>""",
    },
    "cross": {
        "color": "bg-rose-500",
        "icon": """<svg class="h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor"><path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" /></svg>""",
    },
}

template_timeline_children_html = string.Template(
    (
        """
<li>
    <div class="relative pb-8">
        <span class="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200" aria-hidden="true"></span>
        <div class="relative flex space-x-3">
            <div>
                <span class="h-8 w-8 rounded-full ${color} flex items-center justify-center ring-8 ring-white">
                    ${icon}
                </span>
            </div>
            <div class="flex min-w-0 flex-1 justify-between space-x-4 pt-1.5">
                <div>
                    <p class="text-sm text-gray-500">${action} <span class="font-medium text-gray-900">${name}</span></p>
                    <p class="mt-2 text-sm text-gray-500">${description}</p>
                </div>
                <div class="whitespace-nowrap text-right text-sm text-gray-500">
                    <time>${time}</time>
                </div>
            </div>
        </div>
    </div>
</li>
"""
    )
)

template_timeline_parent_html = string.Template(
    (
        """
<script src="https://cdn.tailwindcss.com"></script>
<div class="flow-root max-w-prose">
  <ul role="list" class="-mb-8">
   ${children}
  </ul>
</div>
"""
    )
)

def generate_html_timeline(items):
    timeline_children_html = ""

    for item in items:
        description = item.get("description", "")
        if description.startswith(img_token):
            description = description[len(img_token):]
            ya = YAIGAttachments.from_json(description)
            description = ""
            for url in ya.urls:
                description += f"<img src={url} />"

        timeline_children_html += template_timeline_children_html.safe_substitute(
            color=icon_design[item.get("icon", "actor")]["color"],
            icon=icon_design[item.get("icon", "actor")]["icon"],
            time=item.get("time", ""),
            action=item.get("action", ""),
            name=item.get("name", ""),
            description=description,
        )

    timeline_parent_html = template_timeline_parent_html.safe_substitute(
        children=timeline_children_html
    )

    return timeline_parent_html


async def generate_view(url):
    async with libsql_client.Client(url) as client:
        t = int((datetime.now() - timedelta(days = 3)).timestamp())
        stmt = f"SELECT * FROM messages WHERE created_at >= {str(t)} ORDER BY created_at DESC"
        data = await client.execute(stmt)

    items = []
    for row in data.rows:
        items.append(
            {
                "time": datetime.fromtimestamp(row["created_at"]).strftime("%m/%d/%Y, %H:%M:%S"),
                "icon": "check",
                "action": row["author"],
                "name": "in " + row["channel"] + ", # of reactions: " + str(row["reactions"]),
                "description": row["message"]
            }
        )

    html_timeline = dp.HTML(generate_html_timeline(items))
    return dp.View(html_timeline)


def get_messages_view():
    url = os.getenv("LIBSQL_URL")
    view = asyncio.run(generate_view(url))
    v = dp.View(
        dp.Text("# Latest YAIG hot messages"),
        view
    )
    return v

if __name__ == "__main__":
    dp.serve(get_messages_view)
