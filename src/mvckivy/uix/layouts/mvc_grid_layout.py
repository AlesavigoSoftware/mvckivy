from kivymd.uix.gridlayout import MDGridLayout

from mvckivy.uix.behaviors import MVCBehavior


class GridRow:
    def __init__(self, layout, row_index):
        self.layout = layout
        self.row_index = row_index

    def __getitem__(self, col_index):
        if not self.layout.cols or not self.layout.rows:
            raise ValueError("GridLayout cols and rows must be set")

        if self.row_index >= self.layout.rows or col_index >= self.layout.cols:
            raise IndexError("Index out of range")

        idx_iter = self.layout._create_idx_iter(self.layout.cols, self.layout.rows)
        for idx, (col, row) in enumerate(idx_iter):
            if row == self.row_index and col == col_index:
                return self.layout.children[len(self.layout.children) - 1 - idx]

        return


class MVCGridLayout(MVCBehavior, MDGridLayout):
    def __getitem__(self, row_index):
        if not self.cols or not self.rows:
            raise ValueError("GridLayout cols and rows must be set")

        if row_index >= self.rows:
            raise IndexError("Index out of range")

        return GridRow(self, row_index)
