from bs4 import BeautifulSoup


class FilterHandler:
    def __init__(self, file_path):
        self._file_path = file_path
        self._bs_data = None

    def load_filter(self):
        with open(self._file_path, 'r') as filter_file:
            data = filter_file.read()
            self._bs_data = BeautifulSoup(data, "xml")

    def save_filter(self):
        with open(self._file_path, 'w') as filter_file:
            filter_file.write(self._bs_data.prettify())

    def get_ip(self):
        return self._bs_data.find('SensorIPAddr').get('v')

    def set_ip(self, val):
        self._bs_data.find('SensorIPAddr')['v'] = val


if __name__ == "__main__":
    f = FilterHandler(file_path='filter.xml')
    f.load_filter()
    f.set_ip('192.168.170.3')
    # f.save_filter()

