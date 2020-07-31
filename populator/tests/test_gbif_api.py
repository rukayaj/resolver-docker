import gbif_api
from unittest import TestCase
import responses

class GbifApiTest(TestCase):
    GBIF_API_DATASET_URL = "https://api.gbif.org/v1/dataset/{}"
    endpoints_example = [{'type': 'EML', 'url': 'http://data.gbif.no/eml.do?r=dataset'}, {'type': 'DWC_ARCHIVE', 'url': 'http://data.gbif.no/archive.do?r=dataset'}, {'type': 'DWC_ARCHIVE', 'url': 'old-and-invalid'}]

    @responses.activate
    def test_get_dataset_list(self):
        mock_datasets = [{'key': 'b124e1e0-4755-430f-9eab-894f25a9b59c'}, {'key': 'd34ed8a4-d3cb-473c-a11c-79c5fec4d649'}, {'key': 'd34ed8a4-d3cb-473c-a11c-79c5fec4d649'}]
        mock_json = {'offset': 0, 'limit': 200, 'endOfRecords': 1, 'count': 200, 'results': mock_datasets}
        api_url = self.GBIF_API_DATASET_URL.format('search?limit=5000&publishingCountry=NO')
        responses.add(responses.GET, api_url, json=mock_json, status=200)  # A mock for the API call

        dataset_list = gbif_api.get_dataset_list()
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, api_url)
        self.assertEqual(dataset_list, mock_datasets)

    @responses.activate
    def test_get_dataset_list_api_fail(self):
        url = self.GBIF_API_DATASET_URL.format('search?limit=5000&publishingCountry=NO')
        responses.add(responses.GET, url, json={}, status=500)
        with self.assertLogs() as cm:
            dataset_list = gbif_api.get_dataset_list()
            self.assertTrue('WARNING:root:GET request code: 500. URL: https://api.gbif.org/v1/dataset/search?limit=5000&publishingCountry=NO' in cm.output[0])

    @responses.activate
    def test_get_dataset_detailed_info(self):
        key = 'd34ed8a4-d3cb-473c-a11c-79c5fec4d649'
        url = self.GBIF_API_DATASET_URL.format(key)
        json = {'key': key, 'endpoints': self.endpoints_example, 'label': 'My dataset name', 'doi': 'https://purl.org/my-dataset-doi'}
        responses.add(responses.GET, url, json=json, status=200)

        dataset_info = gbif_api.get_dataset_detailed_info(key)
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, url)
        self.assertEqual(dataset_info, json)

    @responses.activate
    def test_get_dataset_detailed_info_api_fail(self):
        key = 'd34ed8a4-d3cb-473c-a11c-79c5fec4d649'
        url = self.GBIF_API_DATASET_URL.format(key)
        responses.add(responses.GET, url, json={}, status=404)
        with self.assertLogs() as cm:
            dataset_endpoints = gbif_api.get_dataset_detailed_info(key)
            self.assertTrue('WARNING:root:GET request code: 404' in cm.output[0])

    def test_get_dwc_endpoint(self):
        self.assertEqual(gbif_api.get_dwc_endpoint(self.endpoints_example), self.endpoints_example[1])

    def test_get_dwc_endpoint_fail(self):
        metadata_endpoint = [{'key': 364340, 'type': 'EML', 'url': 'http://data.nina.no:8080/ipt/eml.do?r=opensea_seabirds'}]
        self.assertEqual(gbif_api.get_dwc_endpoint(metadata_endpoint), False)

    @responses.activate
    def test_get_cores_from_ipt(self):
        url = 'https://data.gbif.no/ipt/archive.do?r=o_vxl'
        with open('tests/mock_data/dwc_archive_test_file.zip', 'rb') as dwc_zip_stream:
            responses.add(responses.GET, url, body=dwc_zip_stream.read(), status=200, content_type='application/zip', stream=True)

        cores = gbif_api.get_cores_from_ipt(url)
        self.assertEqual(len(cores), 1)
        self.assertEqual(cores[0][0], 'occurrence')
        retrieved_first_line = cores[0][1].readline()
        first_line = b'id\tmodified\tinstitutionCode\tcollectionCode\tbasisOfRecord\toccurrenceID\tcatalogNumber\trecordedBy\tindividualCount\tsex\tpreparations\totherCatalogNumbers\tassociatedMedia\tsamplingProtocol\teventTime\tyear\tmonth\tday\thabitat\tfieldNumber\teventRemarks\tcontinent\tcountry\tstateProvince\tcounty\tlocality\tminimumElevationInMeters\tmaximumElevationInMeters\tminimumDepthInMeters\tmaximumDepthInMeters\tdecimalLatitude\tdecimalLongitude\tcoordinateUncertaintyInMeters\tidentifiedBy\tdateIdentified\ttypeStatus\tscientificName\tkingdom\tphylum\tclass\torder\tfamily\tgenus\tspecificEpithet\tinfraspecificEpithet\tscientificNameAuthorship\n'
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, url)
        self.assertEqual(retrieved_first_line, first_line)

    @responses.activate
    def test_get_cores_from_ipt_fail(self):
        url = 'https://data.gbif.no/ipt/archive.do?r=o_vxl'
        responses.add(responses.GET, url, json={}, status=404)
        with self.assertLogs() as cm:
            retrieved_zip = gbif_api.get_cores_from_ipt(url)
            self.assertTrue('WARNING:root:GET request code: 404' in cm.output[0])

