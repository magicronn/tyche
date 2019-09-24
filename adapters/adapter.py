from abc import ABC, abstractmethod


class Adapter(ABC):

    def __init__(self):
        super().__init__()

    @abstractmethod
    def load_option_csv(self, symbol):
        pass

    @abstractmethod
    def load_quote_csv(self, symbol):
        pass
