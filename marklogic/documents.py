import json
from requests import Session
from urllib3.fields import RequestField
from urllib3.filepost import encode_multipart_formdata


class Document:
    """
    :param uri: the URI of the document; can be None when relying on MarkLogic to
    generate a URI.
    :param content: the content of the document.
    :param content_type: the MIME type of the document; use when MarkLogic cannot
    determine the MIME type based on the URI.
    :param extension: specifies a suffix for a URI generated by MarkLogic.
    :param directory: specifies a prefix for a URI generated by MarkLogic.
    :param repair: for an XML document, the level of XML repair to perform; can be
    "full" or "none", with "none" being the default.
    :param version_id: affects updates when optimistic locking is enabled; see
    https://docs.marklogic.com/REST/POST/v1/documents for more information.
    :param temporal_document: the logical document URI for a document written to a
    temporal collection; requires that a "temporal-collection" parameter be included in
    the request.
    """

    def __init__(
        self,
        uri: str,
        content,
        content_type: str = None,
        extension: str = None,
        directory: str = None,
        repair: str = None,
        extract: str = None,
        version_id: str = None,
        temporal_document: str = None,
    ):
        self.uri = uri
        self.content = content
        self.content_type = content_type
        self.extension = extension
        self.directory = directory
        self.repair = repair
        self.extract = extract
        self.version_id = version_id
        self.temporal_document = temporal_document

    def to_request_field(self) -> RequestField:
        data = self.content
        if type(data) is dict:
            data = json.dumps(data)
        field = RequestField(name=self.uri, data=data, filename=self.uri)
        field.make_multipart(
            content_disposition=self._make_disposition(),
            content_type=self.content_type,
        )
        return field

    def _make_disposition(self) -> str:
        disposition = "attachment"

        if not self.uri:
            disposition = "inline"
            if self.extension:
                disposition = f"{disposition};extension={self.extension}"
            if self.directory:
                disposition = f"{disposition};directory={self.directory}"

        if self.repair:
            disposition = f"{disposition};repair={self.repair}"

        if self.extract:
            disposition = f"{disposition};extract={self.extract}"

        if self.version_id:
            disposition = f"{disposition};versionId={self.version_id}"

        if self.temporal_document:
            disposition = f"{disposition};temporal-document={self.temporal_document}"

        return disposition


class DocumentManager:
    def __init__(self, session: Session):
        self._session = session

    def write(self, documents: list[Document], **kwargs):
        fields = [self._make_default_metadata_field()]
        for doc in documents:
            fields.append(doc.to_request_field())

        data, content_type = encode_multipart_formdata(fields)

        headers = kwargs.pop("headers", {})
        headers["Content-Type"] = "".join(
            ("multipart/mixed",) + content_type.partition(";")[1:]
        )
        if not headers.get("Accept"):
            headers["Accept"] = "application/json"

        return self._session.post("/v1/documents", data=data, headers=headers, **kwargs)

    def _make_default_metadata_field(self):
        """
        Temporary method to ensure the test user can see written documents. Will be
        removed when this feature is implemented for real.
        """
        metadata_field = RequestField(
            name="request-metadata",
            data=json.dumps(
                {
                    "permissions": [
                        {
                            "role-name": "python-tester",
                            "capabilities": ["read", "update"],
                        }
                    ]
                }
            ),
        )
        metadata_field.make_multipart(
            content_disposition="inline; category=metadata",
            content_type="application/json",
        )
        return metadata_field