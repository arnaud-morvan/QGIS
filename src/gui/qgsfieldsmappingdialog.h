/***************************************************************************
   qgsfieldsmappingdialog.h
    --------------------------------------
   Date                 : December 2016
   Copyright            : (C) 2016 Arnaud Morvan
   Email                : arnaud.morvan@gmail.com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************/

#ifndef QGSFIELDSMAPPINGDIALOG_H
#define QGSFIELDSMAPPINGDIALOG_H

#include <QDialog>
#include <QStyledItemDelegate>

#include "qgis_gui.h"
#include "qgsexpression.h"
#include "qgsexpressioncontext.h"
#include "qgsexpressioncontextgenerator.h"
#include "qgsfields.h"

#include "ui_qgsfieldsmappingdialogbase.h"


/** @ingroup gui
 * Table model to edit a QFieldsMapping.
 * @note added in QGIS 3.0
 * @note not available in Python bindings
 */
class GUI_EXPORT QgsFieldsMappingModel : public QAbstractTableModel, public QgsExpressionContextGenerator
{
    Q_OBJECT

  public:
    QgsFieldsMappingModel( const QgsFields& srcfields, const QgsFields& dstfields, QObject *parent = 0 );

    int rowCount( const QModelIndex& parent = QModelIndex() ) const override;
    int columnCount( const QModelIndex& parent = QModelIndex() ) const override;
    QVariant headerData( int section, Qt::Orientation orientation, int role ) const override;
    QVariant data( const QModelIndex& index, int role = Qt::DisplayRole ) const override;
    bool setData( const QModelIndex & index, const QVariant & value, int role = Qt::EditRole ) override;
    Qt::ItemFlags flags( const QModelIndex &index ) const override;

    QgsExpressionContext createExpressionContext() const override;
    QgsVectorLayer* createTempLayer() const;

    typedef QPair<QString, QString> Line;

  private:
    QVector<Line> mLines;
    QgsFields mSrcFields;
};

class GUI_EXPORT QgsExpressionDelegate : public QStyledItemDelegate
{
    Q_OBJECT

  public:
    QgsExpressionDelegate( QgsExpressionContextGenerator *contextGenerator, QgsVectorLayer *layer, QObject *parent = 0 );
    QWidget* createEditor( QWidget *parent, const QStyleOptionViewItem &option, const QModelIndex &index ) const;
    void  setEditorData( QWidget *editor, const QModelIndex &index ) const;
    void  setModelData( QWidget *editor, QAbstractItemModel *model, const QModelIndex &index ) const;

  private:
    QgsExpressionContextGenerator* mContextGenerator;
    QgsVectorLayer* mLayer;
};

///@endcond


/** \ingroup gui
 * @brief The QgsFieldsMappingDialog class provides a input dialog for mapping between source and destination fields.
 * @note added in 3.0
 */
class GUI_EXPORT QgsFieldsMappingDialog : public QDialog, private Ui::QgsFieldsMappingDialogBase
{
    Q_OBJECT

  public:
    QgsFieldsMappingDialog( const QgsFields& srcfields, const QgsFields& dstfields, QWidget* parent = nullptr );

  private:
    QgsFieldsMappingModel mModel;
};

#endif // QGSFIELDSMAPPINGDIALOG_H
