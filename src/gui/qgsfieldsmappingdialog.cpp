/***************************************************************************
    qgsfieldsmappingdialog.cpp
     --------------------------------------
    Date                 : 08.2017
    Copyright            : (C) 2017 Arnaud Morvan
    Email                : arnaud.morvan@camptocamp.com
 ***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/

#include <QHeaderView>

#include "qgsfieldexpressionwidget.h"
#include "qgsfieldsmappingdialog.h"
#include "qgsproject.h"
#include "qgsvectordataprovider.h"
#include "qgsvectorlayer.h"

QgsFieldsMappingDialog::QgsFieldsMappingDialog( const QgsFields& srcfields, const QgsFields& dstfields, QWidget* parent )
    : QDialog( parent )
    , mModel( srcfields, dstfields, this )
{
  setupUi( this );
  this->fieldsView->setModel( &mModel );
  this->fieldsView->setItemDelegateForColumn( 0, new QgsExpressionDelegate( &mModel, mModel.createTempLayer() ) );
  for ( int i = 0; i < mModel.rowCount( QModelIndex() ); i++ )
  {
    this->fieldsView->openPersistentEditor( mModel.index( 0, i ) );
  }
  this->fieldsView->horizontalHeader()->resizeSections( QHeaderView::ResizeToContents );
}

///@cond PRIVATE
QgsFieldsMappingModel::QgsFieldsMappingModel( const QgsFields& srcfields, const QgsFields& dstfields, QObject *parent ) :
    QAbstractTableModel( parent )
    , mSrcFields( srcfields )
{
  QgsField dstfield;
  int srcfield_index;
  QString srcfield_name;
  Q_FOREACH ( dstfield, dstfields )
  {
    srcfield_name = QString();
    srcfield_index = srcfields.lookupField( dstfield.name() );
    if ( srcfield_index != -1 )
    {
      srcfield_name = srcfields.field( srcfield_index ).name();
    }
    mLines.append( Line( srcfield_name, dstfield.name() ) );
  }
}

int QgsFieldsMappingModel::rowCount( const QModelIndex& parent ) const
{
  Q_UNUSED( parent );
  return mLines.count();
}

int QgsFieldsMappingModel::columnCount( const QModelIndex & parent ) const
{
  Q_UNUSED( parent );
  return 2;
}

QVariant QgsFieldsMappingModel::headerData( int section, Qt::Orientation orientation, int role ) const
{
  if ( orientation == Qt::Horizontal && role == Qt::DisplayRole )
  {
    switch ( section )
    {
      case 0:
        return QObject::tr( "Source expression" );
      case 1:
        return QObject::tr( "Destination field" );
    }
  }
  return QVariant();
}

QVariant QgsFieldsMappingModel::data( const QModelIndex& index, int role ) const
{
  if ( index.row() < 0 ||
       index.row() >= mLines.count() ||
       ( role != Qt::DisplayRole && role != Qt::EditRole ) )
  {
    return QVariant();
  }
  if ( index.column() == 0 )
    return mLines.at( index.row() ).first;
  if ( index.column() == 1 )
    return mLines.at( index.row() ).second;
  return QVariant();
}

bool QgsFieldsMappingModel::setData( const QModelIndex & index, const QVariant & value, int role )
{
  if ( index.row() < 0 || index.row() >= mLines.count() || role != Qt::EditRole )
  {
    return false;
  }
  if ( index.column() == 0 )
  {
    mLines[index.row()].first = value.toString();
  }
  else
  {
    mLines[index.row()].second = value.toString();
  }
  emit dataChanged( index, index );
  return true;
}

Qt::ItemFlags QgsFieldsMappingModel::flags( const QModelIndex &index ) const
{
  return QAbstractTableModel::flags( index ) | Qt::ItemIsEditable;
}

QgsExpressionContext QgsFieldsMappingModel::createExpressionContext() const
{
  QgsExpressionContext context = QgsProject::instance()->createExpressionContext();
  context.setFields( mSrcFields );
  return context;
}

QgsVectorLayer* QgsFieldsMappingModel::createTempLayer() const
{
  QgsVectorLayer* layer = new QgsVectorLayer( "Point", "temp_layer", "memory" );
  layer->dataProvider()->addAttributes( mSrcFields.toList() );
  layer->updateFields();
  return layer;
}

QgsExpressionDelegate::QgsExpressionDelegate( QgsExpressionContextGenerator* contextGenerator, QgsVectorLayer* layer, QObject* parent )
    : QStyledItemDelegate( parent )
    , mContextGenerator( contextGenerator )
    , mLayer( layer )
{
}

QWidget* QgsExpressionDelegate::createEditor( QWidget *parent, const QStyleOptionViewItem &option, const QModelIndex &index ) const
{
  Q_UNUSED( option );
  Q_UNUSED( index );

  QgsFieldExpressionWidget* expressionWidget = new QgsFieldExpressionWidget( parent );
  expressionWidget->registerExpressionContextGenerator( mContextGenerator );
  expressionWidget->setLayer( mLayer );
  return expressionWidget;
}

void QgsExpressionDelegate::setEditorData( QWidget *editor, const QModelIndex &index ) const
{
  QgsFieldExpressionWidget* expressionWidget = static_cast<QgsFieldExpressionWidget*>( editor );
  expressionWidget->setField( index.model()->data( index, Qt::EditRole ).toString() );
}

void QgsExpressionDelegate::setModelData( QWidget *editor, QAbstractItemModel *model, const QModelIndex &index ) const
{
  /*
  elif fieldType == QgsExpression:
      (value, isExpression, isValid) = editor.currentField()
      if isExpression is True:
          model.setData(index, value)
      else:
          model.setData(index, QgsExpression.quotedColumnRef(value))
  */
  QgsFieldExpressionWidget* expressionWidget = static_cast<QgsFieldExpressionWidget*>( editor );
  model->setData( index, expressionWidget->expression() );
}
